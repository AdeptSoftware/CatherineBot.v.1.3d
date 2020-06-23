# Парсер сообщений (версия 2.0) 05.08.2019 (содержимое self.words не менять в других местах!)
import re
from core.instance import app as _app
# не учитывает, если текст-не картинка
_re_word     = re.compile(r"(?:(?:\w+|\d+)-\w+|[_\w\d]+|\[id\d+\|.+?\])")
_re_link     = re.compile(r"\[id(\d+)\|.+?\]")
_re_nick     = re.compile(r"^[_A-Za-z0-9]{3,16}$")
_re_cyrillic = re.compile(r"^[_А-ЯЁа-яё]+$")


""" # декоратор классов
def ro_property(name):
    def ro_property_decorator(c):
        setattr(c, name, property(lambda o: o.__dict__["_" + name]))
        return c
    return ro_property_decorator
@ro_property('prefix')
"""


class Parser:
    # space_ignore - игнорировать пробелы в self.prefix и self.words[i][2]
    def __init__(self, text, space_ignore=True):
        self.prefix = ''        # если перед строкой стоят какое-то символы Not (0-9, А-Я, A-Z)
        self.words = []         # все слова + стоящие после них знаки: ["Слово", "слово", "!"]
        self.length = 0         # размер self.words
        self.sentences = []     # начало и конец предложения (end-1 || < end)
        self._parser(text, space_ignore)

    def _parser(self, text, space_ignore):
        i = 0
        last_span = 0
        for obj in _re_word.finditer(text):
            self.words += [["", "", ""]]
            span = obj.span()
            if span[0]-last_span > 0:
                self._add_symbols(text, i, last_span, span[0], space_ignore)
            self.words[i][0] += text[span[0]:span[1]]
            self.words[i][1] += self.words[i][0].lower()
            last_span = span[1]
            i += 1
        length = len(text)
        len_s = len(self.sentences)
        if last_span != length or (len_s == 0 and len(self.words) > 0) or \
           (len_s != 0 and self.sentences[len_s-1][1] < length):
            self._add_symbols(text, i, last_span, length, space_ignore, True)
        if self.prefix != "":
            data = ""
            for char in self.prefix:
                if char not in data:
                    data += char
            self.prefix = [self.prefix, data]
        else:
            self.prefix = ["", ""]
        self.length = len(self.words)
        if self.length == 0:
            self.sentences = None

    def _add_symbols(self, text, i, span0, span1, space_ignore, new_sentences=False):
        data = text[span0:span1]
        if space_ignore:
            data = ''.join(data.split(' '))
        if i > 0:
            self.words[i-1][2] += data
        else:
            self.prefix += data
        if not new_sentences:
            for char in ',.?!():;[]':
                if char in self.words[i-1][2]:
                    new_sentences = True
                    break
        if new_sentences:
            length = len(self.sentences)
            if length == 0:
                self.sentences += [[0, i]]
            else:
                self.sentences += [[self.sentences[length-1][1], i]]


def _reference_mask(mp, refs):
    if mp.sentences is None or refs is None:
        return
    for s_obj in mp.sentences:
        s_obj += [False]
    # начнем анализ
    s = [0]
    while s[0] < len(mp.sentences):
        if not _update_mp(mp, refs, s, 0):          # в начале предложения
            _update_mp(mp, refs, s, 1)              # в конце преложения
        s[0] += 1
    # избавимся от вспомогательной переменной
    s = 0
    while s < len(mp.sentences):
        if mp.sentences[s][2]:
            mp.sentences_ref += [s]
        mp.sentences[s].pop(2)
        s += 1
    mp.length = len(mp.words)


def _update_mp(mp, refs, s, index):
    pos = mp.sentences[s[0]][index]-index
    if mp.words[pos][1] in refs:
        # Все возможные варианты (x - mp.words[i]; ? - какой-то сепаратор кроме ','; ! - из-за смещения стало s[0]+1;
        # Если refs[i] справа от x: index=0, слева: index=1. Для refs[i] текущее предложение s[0];
        # _s - mp.sentences; d - mp.sentences.pop(offset) -w - mp.words.pop(pos); # - не важно; o++ = _s[s[0]][0]++;
        #  o - сместить все значения в _s начиная с #; o-- = _s[s[0]][1]--; t - кому присвоить ref;
        # -с - удалить символ с предыдущего слова; -a - добавить предыдущему слову символы из текущего list=sym+list
        # Этапы:                            #  1     2          3          4                   Уникальное
        #        x refs[i] x                # не может существовать для всех pos
        # s[0]-1 ? refs[i] x                # -w; o++       o[s[0]];    t[s[0]];
        # s[0]-1 , refs[i] x                # -w; o++       o[s[0]];    t[s[0]];
        #          refs[i] x                # -w;           o[s[0]];    t[s[0]];
        #        x refs[i] ? s[0]+1         # -w; o--;      o[s[0]+1];  t[s[0]];            -a;
        # s[0]-1 ? refs[i] ? s[0]+1         # -w; d[s[0]];  o[!s[0]];   t[!s[0]];           -a;
        # s[0]-1 , refs[i] ? s[0]+1         # -w; d[s[0]];  o[!s[0]];   t[s[0]-1];  -c[,];  -a;
        #          refs[i] ? s[0]+1         # -w; d[s[0]];  o[!s[0]];   t[!s[0]];
        #        x refs[i] , s[0]+1         # -w; o--;      o[s[0]+1];  t[s[0]];            -a;
        # s[0]-1 ? refs[i] , s[0]+1         # -w; d[s[0]];  o[!s[0]];   t[!s[0]]
        # s[0]-1 , refs[i] , s[0]+1         # -w; d[s[0]];  o[!s[0]];   t[!s[0]-1]  _s[s[0]-1][1]=_s[!s[0]][1]; d[!s[0]]; -c[,];
        #          refs[i] , s[0]+1         # -w; d[s[0]];  o[!s[0]];   t[!s[0]]
        #        x refs[i]                  # -w; o--;                  t[s[0]];
        # s[0]-1 ? refs[i]                  # -w; d[s[0]];              t[s[0]-1];
        # s[0]-1 , refs[i]                  # -w; d[s[0]];              t[s[0]-1];
        #          refs[i]                  # -w; d[s[0]];

        # Этап #1 и подготовительные операции
        c_last = ""                                          # Одно из состояний для c_last и c_current: '?', ',', ''
        c_current = mp.words.pop(pos)[2]                     # -w
        if pos > 0:
            c_last = mp.words[pos-1][2]
        if c_last == "" and pos > 0 and c_current == "" and pos != len(mp.words):
            return True                                      # идем к следующему "предложению".
        len_s = mp.sentences[s[0]][1]-mp.sentences[s[0]][0]-1
        # Этап #2
        flag_x_left = (index == 1 and len_s > 0)
        if flag_x_left:                                      # есть x перед refs[i]
            mp.sentences[s[0]][1] -= 1                       # o--
        elif len_s == 0:
            mp.sentences.pop(s[0])                           # d[s[0]]
        if c_last != "" and len_s > 0:
            mp.sentences[s[0]][0] += 1                       # o++
        # Этап #3
        flag_x_not_right = (pos+1 >= len(mp.words))
        if not flag_x_not_right or (len(mp.words) == 1 and mp.words[0][1] not in refs):
            offset = 0
            if flag_x_left:                                  # есть x перед refs[i]
                offset = 1
            for i in range(s[0]+offset, len(mp.sentences)):  # o[s[0]+offset]
                if mp.sentences[i][0] > 0:
                    mp.sentences[i][0] -= 1
                mp.sentences[i][1] -= 1
        # Этап #4
        if len(mp.words) > 0:                                # not (refs[i])
            offset = 0
            if (',' in c_last and c_current != "") or (flag_x_not_right and c_last != ""):
                offset = -1
            mp.sentences[s[0]+offset][2] = True              # t[s[0]+offset]
        # Уникальные (завершающие операции)
        # после refs[i] стоит ?
        if c_current != "" and ',' in c_last:
            mp.words[pos-1][2] = c_last.replace(',', '', 1)  # -c[,]
        if (flag_x_left and c_current != "") or (c_last != "" and c_current != "" and ',' not in c_current):
            mp.words[pos-1][2] = c_current                   # -a
        if ',' in c_last and ',' in c_current:
            if s[0] < len(mp.sentences):
                mp.sentences[s[0]-1][1] = mp.sentences[s[0]][1]  # _s[s[0]-1][1]=_s[!s[0]][1]
                mp.sentences.pop(s[0])
            mp.words[pos-1][2] = c_current.replace(',', '', 1)
        return True
    return False                                             # смотрим дальше


def _pop_word(mp, s, pos):
    mp.words.pop(pos)
    mp.sentences[s][1] -= 1
    for i in range(s + 1, len(mp.sentences)):
        mp.sentences[i][0] -= 1
        mp.sentences[i][1] -= 1


class MessageParser(Parser):
    # mask - обработчик класса, вносящий изменения в класс
    def __init__(self, item, refs=None, replace_yo=True, mask=_reference_mask, group=None):
        if replace_yo:
            item["text"] = item["text"].replace('ё', 'е')
        self.sentences_ref = []                 # В каких предложениях было обращение к боту
        super().__init__(item["text"])
        # дополнительные поля для MessageParser
        self.node  = None                        # Текущий Node
        # из профиля пользователя
        self.group = group
        self.nick  = None
        self.name  = None
        self.is_man = True
        # из сообщения
        self.item = item
        self.pid = self.item.pop("peer_id")
        self.uid = self.item.pop("from_id")

        self.fwd = []
        if "fwd_messages" in self.item:
            self.fwd += self.item.pop("fwd_messages")
        if "reply_message" in self.item:
            self.fwd += [self.item.pop("reply_message")]

        # прочие обработчики
        mask(self, refs)
        self._load_profile()

    def get_sentence(self, index, is_lower=False):
        if index < 0 or index >= len(self.sentences):
            return ""
        msg = ""
        for i in range(self.sentences[index][0], self.sentences[index][1]):
            msg += self.words[i][int(is_lower)] + self.words[i][2] + ' '
        return msg[:len(msg)-1]

    def find_nicknames(self, in_text=True, in_fwd_messages=True, unk=False, count=-1, is_all=True):
        if not in_text and not in_fwd_messages:
            return None
        users_id = {}   # пользователь-ник
        unknowns = []   # потенциальные ники
        # если надо добавим свой ник

        # Проверим сообщение на наличие ников, ссылок вида @id, @domain
        if in_text:
            i, pos = 1, len(self.words[0][0])+1
            while i < self.length:
                if self.group == "Vainglory" and self.words[i] in ["3x3", "5x5", "3vs3", "5vs5", "3v3", "5v5", "rank"]:
                    i += 1
                    continue
                res = _re_link.findall(self.words[i][1])
                if len(res) != 0:
                    res[0] = int(res[0])
                    users_id[res[0]] = _app().disk.user_profile(res[0]).nick(None, is_all, None)
                else:
                    if self.group == "Vainglory":
                        _n, _id = self.words[i][0], None
                        if _re_nick.match(_n) is not None:
                            _id = _app().disk.user_profile(self.words[i][0], self.group).key("id", None)
                        else:
                            i += 1
                            continue
                    else:
                        _n, _id = "", None
                        while i < self.length:
                            if '\n' in self.words[i][2]:
                                break
                            i += 1
                        while pos < len(self.item["text"]):
                            if self.item["text"][pos] == '\n':
                                pos += 1
                                break
                            _n += self.item["text"][pos]
                            pos += 1
                        if pos-2 >= 0 and self.item["text"][pos-1] == '\n' and self.item["text"][pos-2] == ' ':
                            _n = _n[:-1]
                        if _n == "":
                            i += 1
                            continue
                        u = _app().disk.user_profile(_n, self.group)
                        if self.group is None and u.group(_n) is not None:
                            _n += ' (%s)' % str(u.group(_n))
                        _id = u.key("id", None)
                    if _id is not None and _id not in users_id:
                        if is_all:
                            users_id[_id] = [_n]
                        else:
                            users_id[_id] = _n
                    else:
                        if unk and _n != "" and _n not in unknowns:
                            unknowns += [_n]
                if 0 < count <= len(users_id):
                    if unk:
                        return users_id, unknowns
                    return users_id
                i += 1
        # Проверим пересланные сообщения
        if in_fwd_messages:
            for item in self.fwd:
                if item["from_id"] not in users_id and item["from_id"] > 0 and item["from_id"] not in users_id:
                    users_id[item["from_id"]] = _app().disk.user_profile(item["from_id"]).nick(self.group, is_all, None)
                else:
                    if unk and item["from_id"] not in unknowns and item["from_id"] not in users_id:
                        unknowns += [item["from_id"]]
                if 0 < count <= len(users_id):
                    break
        if unk:
            return users_id, unknowns
        return users_id

    def ref(self, get_nick=False, add_link=False, default=None):
        p = None
        if get_nick and self.nick is not None:
            p = self.nick[0]
        elif not get_nick and self.name is not None:
            p = self.name
        if p is None:
            if default is not None:
                p = str(default)
            else:
                if self.nick is not None:
                    p = self.nick[0]
                elif self.name is not None:
                    p = self.name
                else:
                    p = "@id"+str(self.uid)
        if add_link:
            return "[id{0}|{1}]".format(self.uid, p)
        return p

    def _load_profile(self):
        u = _app().disk.user_profile(self.uid)
        if u.is_exist():
            self.nick = u.nick(self.group, True, None)
            self.name = u.key("first_name", "?")
            self.is_man = (u.key("sex", 2) == 2)
        self.s = _app().disk.s_get(self.uid)

    # не защищено от выхода за пределы массива
    def is_cyrillic_word(self, index):
        return _re_cyrillic.match(self.words[index][0]) is not None

    def send(self, text, attachment=None, do_not_parse_links=True, block_ref=False, peer_id=None):
        if not block_ref and text != "" and self.node is not None and self.node.is_ref():
            text = self.ref() + ", " + text
        if peer_id is None:
            peer_id = self.pid
        _app().vk.send(peer_id, text, attachment, do_not_parse_links)
        return 1    # FN_BREAK

    # склонение
    @staticmethod
    def transform(text):
        if text == "":
            return "Он(а)"
        lo = text.lower()
        if lo == "себя":
            return "Ты"
        if lo == "всех":
            return "Все"
        if lo == "игоря":
            return "Игорь"
        if lo == "павла":
            return "Павел"
        if 'а' <= text[0] <= 'я':
            text = text[0].upper() + text[1:]
        sym = {'а': '', 'у': 'а', 'ю': 'я', 'я': 'й'}
        c = text[len(text) - 1]
        for t in sym:
            if t == c:
                return text[:len(text) - 1] + sym[t]
        return text
