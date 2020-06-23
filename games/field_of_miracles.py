# 16.04.2019
import games.db_vainglory as db
import core.event.eventer
import core.utils.fnmsg
from core.instance import *
import random
import time
import re


class FieldOfMiracles:
    def __init__(self):
        self._vgd = db.R([db.create(), db.item()])
        self._ids = []                          # список участников
        self._pos = 0                           # текущий id
        self._word = ""                         # загаданное слово
        self._word_pos = []                     # позиция загаданного слова, от которого зависит вопрос
        self._chars = ""                        # символы, которые были
        self._win_chars = ""                    # буквы которые надо угадать для победы
        self._symbol = "&#10052;"               # символ, на который заменяется *
        self._space = '_'          # "&#128293;"
        self._print = []                        # текст, который будет выводиться на экран
        self._comment_char = '-'                # символ комментария
        self._template = []                     # шаблон

        self._pid = None
        self._max_wait = 60                     # макс. время ожидания хода
        self._time_next = time.time()

        self._on_pass = ["пас", "покинуть"]
        self._on_begin = ["начать", "старт", "вступить"]
        self._on_win = ["Победил(-а) {0}! Поздравляю!"]
        self._on_begin_game = ["{0} вступил(-а) в игру!"]
        self._on_end_game = ["{0} покинул(-а) игру!"]
        self._on_time = ["{0} ваше время истекло! Ход перешел к {1}"]
        self._on_repeat = ["{1}, буква '{0}' уже была!\nВаш ход перешел к {2}"]
        self._on_miss_sym = ["{0}, такого нет в загаданном!\nВаш ход перешел к {1}!"]
        self._on_miss = ["{0}, Ваш ход чуть позже. Подождите!"]

    def get_answer(self):
        return self._word

    def get_comment_char(self):
        return self._comment_char

    def analyze(self, ps, first_name):
        # анализ списка игроков
        is_in_game = False
        current = None
        for u in self._ids:
            if u[0] == ps.item["from_id"]:
                is_in_game = True
                if u == self._ids[self._pos]:
                    current = u
                    break
        # анализ текста
        text = ps.item["text"].lower()
        if is_in_game:
            # хочет ли игрок выйти из игры?
            for key in self._on_pass:
                if key == text:
                    self.remove(first_name, ps.item["from_id"])
                    return True
            if current is not None:
                if text == self._word.lower():
                    # угадал слово
                    self._win(first_name)
                elif len(text) == 1:
                    # пользователь сказал букву
                    if text not in self._chars:
                        # и такой буквы не было
                        self._chars += text
                        if text not in self._word.lower():
                            # даже в загаданном слове
                            msg = _get(self._on_miss_sym).format(first_name, self._next())
                            app().vk.send(self._pid, msg)
                            self.print()
                        else:
                            # есть такая буква
                            self._win_chars += text
                            self._update_text()
                            if self._word == _view(self._print, self._space):
                                # угадали букву и слово целиком
                                self._win(first_name)
                            else:
                                # продолжаем
                                self.print()
                    else:
                        # такая буква уже была
                        msg = _get(self._on_repeat).format(text, first_name, self._next())
                        app().vk.send(self._pid, msg)
                        self.print()
                else:
                    flag = False
                    wx = self._word.lower()
                    for w in ps.words:
                        if w[1] in wx:
                            pos = wx.find(w[1])
                            for p in range(pos, pos+len(w[1])):
                                self._template[p] = self._word[p]
                            self._update_text()
                            flag = True
                            break
                    if not flag:
                        # не угадали
                        msg = _get(self._on_miss_sym).format(first_name, self._next())
                        app().vk.send(self._pid, msg)
                        self.print()
                    else:
                        if self._word == _view(self._print, self._space):
                            self._win(first_name)
                        else:
                            self.print()
            else:
                # очередь не этого игрока
                if len(text) == 1:
                    app().vk.send(self._pid, _get(self._on_miss).format(first_name))
                    self.print("Ходит [[id{0}|{1}]]\n".format(self._ids[self._pos][0], self._ids[self._pos][1]))
            return True
        else:
            # если игрок есть, то не запускать заново и не добавлять его
            for u in self._ids:
                if u[0] == ps.item["from_id"]:
                    return True
            # хочет ли игрок вступить в игру?
            for key in self._on_begin:
                if key == text:
                    self._pid = ps.item["peer_id"]
                    if len(self._ids) == 0:
                        self.new_game()
                    self._ids += [[ps.item["from_id"], first_name]]
                    msg = _get(self._on_begin_game).format(first_name)
                    app().vk.send(self._pid, msg)
                    return True
        return False

    def _win(self, name):
        msg = _get(self._on_win).format(name)+'\nХодит '+self._next()
        app().vk.send(self._pid, msg)
        self.new_game()

    def _next(self):
        self._pos += 1
        if self._pos >= len(self._ids):
            self._pos = 0
        if len(self._ids) != 0:
            return "[[id{0}|{1}]]".format(self._ids[self._pos][0], self._ids[self._pos][1])
        return ""

    def _question(self):
        if len(self._word_pos) == 0:
            return ""
        if self._word_pos[0] == 0:
            if self._word_pos[2] == 0:
                return "Отгадайте умение. "
            elif self._word_pos[2] == 1:
                return "Отгадайте талант. "
            elif self._word_pos[2] == 2:
                return "Отгадайте образ. "
            else:
                return "Отгадайте имя персонажа. "
        else:
            p = random.randint(0, 10)
            if p == random.randint(0, 10):
                _text = ""
                if self._word_pos[1] == 0:  # оружие
                    _text += "оружие"
                elif self._word_pos[1] == 1:  # кристалл
                    _text += "кристалл"
                elif self._word_pos[1] == 2:  # защита
                    _text += "защита"
                elif self._word_pos[1] == 3:  # полезное
                    _text += "полезное"
                else:  # другое
                    _text += "другое"
                # return "Отгадайте предмет. "+str(self._word_pos[2]+1)+"ур. из вкладки "+_text+": "
                return "Отгадайте предмет: "
            else:
                return "Отгадайте предмет: "

    def _update_text(self):
        # зашифруем слово
        pos = []
        self._ans = ""
        self._print = []
        i = 0
        for p in range(0, len(self._word)):
            if self._template[p] != '':
                self._print += [self._template[p]]
                continue
            if not ('а' <= self._word[p].lower() <= 'я'):
                if self._word[p] != ' ':
                    self._print += [self._word[p]]
                else:
                    self._print += [self._space]
                self._ans += self._word[p]
            else:
                if self._word[p].lower() in self._win_chars:
                    self._print += [self._word[p]]
                else:
                    self._print += [self._symbol]
                pos += [i]
            i += 1
        # облагородим
        word = re.findall(r'[^ \n]+', _view(self._print))
        length = len(word)
        pos = -1
        for i in range(0, length):
            pos += len(word[i])+1
            if self._symbol not in word[i]:
                if i+1 < length and self._symbol not in word[i+1] and self._print[pos] != self._space:
                    self._print[pos] = " "
            else:
                res = re.findall(r''+self._symbol+r'+', word[i])
                pos -= len(res)*(len(self._symbol)-1)

    def print(self, text=""):
        self._time_next = time.time() + self._max_wait
        s = ""
        if self._chars != "":
            s = ' | Исп.: '+''.join(sorted(self._chars))
        _v = _view(self._print)
        app().vk.send(self._pid, text+_v+s)
        return None

    def new_game(self):
        self._word = ""
        self._chars = ""
        self._win_chars = ""
        while self._word == "":
            self._word_pos.clear()
            self._word = self._vgd.get_rnd(self._word_pos)
        self._word.lower().replace('ё', 'е')
        str_x = ""
        for c in self._word:
            if c not in str_x:
                str_x += c
        self._template = ['']*len(self._word)
        self._update_text()
        self.print(self._question())
        # app().vk.console(self._word)

    def remove(self, first_name, user_id):
        user = None
        for u in self._ids:
            if u[0] == user_id:
                user = u
                break
        if user is not None:
            self._ids.remove(user)
            msg = _get(self._on_end_game).format(first_name) + '\n'
            if user_id == user[0]:
                msg += self._next() + '\n'
            app().vk.send(self._pid, msg)
            self._time_next = time.time() + self._max_wait + 10
        else:
            app().vk.send(self._pid, first_name + " - не играет сейчас!")

    # функция апдейта
    def update(self):
        if len(self._ids) != 0:
            if self._time_next <= time.time():
                first_name = self._ids[self._pos][1]
                self._ids.remove(self._ids[self._pos])
                msg = _get(self._on_time).format(first_name, self._next())
                if len(self._ids) == 0:
                    msg += "... Всё? Больше никто не хочет со мной сыграть?"
                app().vk.send(self._pid, msg)
                self._time_next = time.time() + self._max_wait
        return len(self._ids) == 0


def _get(_list, std="?"):
    length = len(_list)
    if length == 0:
        return std
    elif length == 1:
        return _list[0]
    return _list[random.randint(0, length)]


# конверт
def _view(arr, space=' '):
    text = ""
    for string in arr:
        if string == space:
            text += ' '
        else:
            text += string
    return text


_game = None
print("Include Game \"Field of Miracles\"")


# функция апдейта
def _event_fn_update(event):
    global _game
    if _game.update():
        _game = None
        return False
    return True


# избавится от потока, переделать в ивенты
def on_message(e_obj, user, chat_id_target):
    if e_obj["peer_id"] == chat_id_target:
        global _game
        ps = core.utils.fnmsg.MessageParser(e_obj, [])
        ps.peer_id = e_obj["peer_id"]
        if ps.item["from_id"] == 481403141 and _game is not None:
            if ps.item["text"] == "$":
                app().vk.send(ps.peer_id, "Ответ: " + _game.get_answer())
                _game.new_game()
                return True
            elif ps.item["text"] == "$!":
                try:
                    _game.remove("Игрок", ps.item["reply_message"]["from_id"])
                finally:
                    return True
        try:
            first_name = user["user"]["first_name"]
        except Exception as err:
            print(str(err))
            first_name = "Игрок"
        if _game is not None and ps.item["text"] != "" and ps.item["text"][0] == _game.get_comment_char():
            return False
        if _game is None:
            _game = FieldOfMiracles()
            app().eventer.new(core.event.eventer.Event("Field of Miracles", None, _event_fn_update, 1))
        return _game.analyze(ps, first_name)
    return False
