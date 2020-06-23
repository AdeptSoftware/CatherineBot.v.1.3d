# 01.12.2018 Функции и классы для обработки текстовых сообщений
import re
_rc = re.compile(r"(?:(?:\w+|\d+)-\w+|[_\w\d]+)")       # не учитывает, если текст-не картинка
_rs = re.compile(r"[.,!?()\[\]]")


# преобразование символов
def _used_chars(text, i_start=0, i_end=1000000000, u_mode=False, space_ignore=True):
    chars = ""
    for i in range(i_start, i_end):
        if text[i] != ' ' or not space_ignore:
            if (u_mode and text[i] not in chars) or (not u_mode):
                chars += text[i]
    return chars


class Parser:
    # u_mode - перечислить символы только единыжды
    def __init__(self, text, separators=_rs, u_mode=False, space_ignore=True):
        # можно конечно их защищать, но стоит ли?
        self.prefix = ''                # если перед строкой стоят какое-то символы Not (0-9, А-Я, A-Z)
        self.words = []                 # все слова + стоящие после них знаки: ["Слово", "слово", "!"]
        self.sentences = []             # начало и конец предложения (end-1 || < end)
        self._parser(text, separators, u_mode, space_ignore)

    # ==== ========= ========= ========= ========= ========= ========= ==========
    # разбивка текста
    def _parser(self, text, separators, u_mode, space_ignore):
        i = 0
        words = []
        length = len(text)
        while i < length:
            res = _rc.search(text, i, length)
            if res is not None:
                span = res.span()
                i = span[1]
                words += [[text[span[0]:span[1]], span]]
            else:
                break
        if len(words) > 0:
            # определим границы предложений
            # self.sentences имеет вид:     [(начало предложения, начало следующего), ...]
            last = 0
            for i in range(0, len(words) - 1):
                words[i] += [words[i + 1][1][0]]
                sym = separators.search(text, words[i][1][1], words[i + 1][1][0])
                if sym is not None:
                    self.sentences += [[last, i + 1]]
                    last = i + 1
            if len(words) == 1:
                words[0] += [length]
            else:
                words[len(words) - 1] += [length]
            self.sentences += [[last, len(words)]]
            # заполним поля класса
            # self.words имеет вид:         [['LowerCase', 'NormalCase', '.;$'], ...]
            flag = False
            for word in words:
                if not flag:
                    flag = True
                    if word[1][0] != 0:
                        self.prefix = _used_chars(text, 0, word[1][0], u_mode, space_ignore)
                self.words += [[word[0], word[0].lower(), _used_chars(text, word[1][1], word[2], u_mode, space_ignore)]]
        else:
            if length != 0:
                self.prefix = _used_chars(text, 0, length, u_mode, space_ignore)
            self.sentences = None


class MessageParser(Parser):
    def __init__(self, item, ref_list=None, replace_yo=True):
        if replace_yo:
            item["text"] = item["text"].replace('ё', 'е')
        super().__init__(item["text"], _rs, False, True)
        # инициализация переменных
        self.item = item                                    # обрабатываемое сообщение
        self.profile = None                                 # профиль, вызывающего команду
        self.peer_id = None                                 # id диалога, в который надо отослать
        self.node = None                                    # Node - на который среагировали
        
        if ref_list is not None:
            self._check_refs(ref_list)

    def get_word_list(self, index=0, is_lower=False, ignore_empty=True):
        if index >= len(self.words):
            return []
        if index < 0:
            index = 0
        _list = []
        for i in range(index, len(self.words)):
            if ignore_empty and self.words[i][0] == "":
                continue
            _list += [self.words[i][is_lower]]
        return _list

    def _check_refs(self, refs):
        # подготовка
        if self.sentences is None:
            return 
        for s in self.sentences:
            s += [False]
        # анализ
        s = 0
        delete = []
        while s < len(self.sentences):
            if self.sentences[s][1]-self.sentences[s][0] == 1:
                if self.words[self.sentences[s][0]][1] in refs:
                    delete = [s] + delete
                    # проверим, а не надо ли склеить предложение
                    if s != 0 and s != len(self.sentences)-1:
                        if self.words[self.sentences[s-1][1]-1][2] == ',' and \
                           self.words[self.sentences[s][0]][2] == ',':
                            # удалим со смещением
                            self.words[self.sentences[s-1][1]-1][2] = ""
                            self.words.pop(self.sentences[s][0])
                            for x in range(s+1, len(self.sentences)):
                                self.sentences[x][0] -= 1
                                self.sentences[x][1] -= 1
                            # скорректируем
                            delete = [s+1] + delete
                            self.sentences[s-1][1] = self.sentences[s+1][1]
                            self.sentences[s-1][2] = True
                            s -= 1
                            continue
                        elif self.words[self.sentences[s-1][1]-1][2] == ',':
                            delete = [s+1] + delete
                            self.words[self.sentences[s-1][1]-1][2] = ""
                            self.sentences[s-1][2] = True
                    elif s == len(self.sentences)-1:
                        if s-1 >= 0:
                            self.words[self.sentences[s-1][1]-1][2] = ""
                            self.sentences[s-1][2] = True
                    else:
                        if s+1 < len(self.sentences):
                            self.sentences[s+1][2] = True
                # else: pass
            else:
                if self.words[self.sentences[s][0]][1] in refs:
                    self.sentences[s][2] = True
                    self.sentences[s][0] += 1
                if self.words[self.sentences[s][1]-1][1] in refs:
                    self.sentences[s][2] = True
                    self.sentences[s][1] -= 1
            s += 1
        for d in delete:
            self.sentences.pop(d)





