# 02.01.2019
import core.utils.fnstr


# константы для _C._type
COND_C_ANY = 0
COND_C_FIRST = 1
COND_C_LAST = -1

# константы для _M.mode
COND_M_ANY = 0
COND_M_LEFT = -1
COND_M_RIGHT = 1

# константы для символа в конце
COND_Q_NONE = 0
COND_Q_YES = 1
COND_Q_NO = 2


# ======== ========= ========= ========= ========= ========= ========= =========
# сравнение ключей
def _cmp_key(data, words, i, is_lower):
    length = len(words)
    # проверим исключения
    if "ex" in data:
        for exc in data["ex"]:
            pos = i+exc[1]
            if exc[1] != 0 and (pos < 0 or pos >= length):
                continue
            for e in exc[0]:
                if _chk(words[pos][is_lower], e, data["ex_dist"]):
                    return False
    # проверим ключ
    for key in data["keys"][0]:
        if "s" in data:
            for s in data["s"]:
                if _chk(words[i][is_lower], key+s, data["keys_dist"]):
                    return True
        else:
            if _chk(words[i][is_lower], key, data["keys_dist"]):
                return True
    return False


def _chk(word, key, dist):
    if word == key or (dist is not None and core.utils.fnstr.distance(word, key) <= dist):
        return True
    return False


# преобразование ключей
def _transform_keys(keys):
    if keys is None:
        return None
    for i in range(0, len(keys)):
        if ' ' in keys[i]:
            keys[i] = keys[i].split()
    return keys


# генерация ключей
# ex: [[["a", "b", ...], offset], ...]
def keygen(keys, s=None, e=None, keys_dist=None, ex_dist=None):
    if type(keys) is str:
        keys = [keys]
    data = {"keys": [keys], "keys_dist": keys_dist}
    if s is not None:
        data["s"] = s
    if e is not None:
        data["ex"] = e
        data["ex_dist"] = ex_dist
    return data


def ex(keys, offset=0):
    if type(keys) is str:
        return [[keys], offset]
    return [keys, offset]


# Возвращает Condition
def n(key_list, _type=COND_C_ANY, q=COND_Q_NONE, max_sentences=-1, only_lower=True):
    cond = Condition(q, max_sentences)
    cond.c(key_list, _type, only_lower)
    return cond


# ======== ========= ========= ========= ========= ========= ========= =========
# проверить ключи (позднее названо условием)
def _check_condition(words, i, is_lower, cond):
    if cond is None:
        return 1        # любое слово по данной позиции
    for obj in cond:
        _type = type(obj)
        if _type is str:
            if words[i][is_lower] == obj:
                return 1
        elif _type is dict:
            if _cmp_key(obj, words, i, is_lower):
                return 1
        elif _type is list:
            length = len(obj)
            if i+length <= len(words):
                x = i
                flag = True
                for w in obj:
                    if words[x][is_lower] != w:
                        flag = False
                        break
                    x += 1
                if not flag:
                    continue
                return length
        else:
            try:
                if obj(words, i, is_lower):
                    return 1
            except Exception as err:
                print(str(err)+": "+str(type(obj))+" вызвали как функцию!.\nargs:\n"+str(words)+'\n'+str(i))
    return 0


# для работы с условиями и модификаторами
class M:
    # offset:
    #     0 - смещение неизвестно, стоит где-то в тексте правее/левее
    # m_: (учитывается только когда offset == 0
    #    COND_M_LEFT - левее, COND_M_ANY - не важно, COND_M_RIGHT - правее
    def __init__(self, cond, offset=0, m_=COND_M_ANY, only_lower=True):
        self.cond = _transform_keys(cond)
        self.only_lower = only_lower
        self.mode = m_
        self.offset = offset


# для работы с условиями и модификаторами
class C:
    # c_type:
    #    COND_C_LAST  - стоит в конце предложения (недоступен mode == COND_M_RIGHT)
    #    COND_C_ANY   - стоит где-то в предложении
    #    COND_C_FIRST - стоит в начале предложения  (недоступен mode == COND_M_LEFT)
    def __init__(self, cond, c_=COND_C_ANY, only_lower=True):
        self._mods = []
        self._cond = _transform_keys(cond)
        self._only_lower = only_lower
        if c_ in [COND_C_FIRST, COND_C_ANY, COND_C_LAST]:
            self._type = c_
        else:
            print("Тип условия неизвестен! Установлен по умолчанию COND_C_ANY!")
            self._type = COND_C_ANY

    def get_type(self):
        return self._type

    def set_mod(self, mod):
        self._mods += [mod]

    # существует ли такое смещение?
    def is_have_offset(self, offset):
        for mod in self._mods:
            if mod.offset == offset:
                return True
        return False

    # проверка по индексу
    def _check(self, words, i, i_start, i_end):
        used = []
        # начнем проверять...
        res = _check_condition(words, i, self._only_lower, self._cond)
        if res != 0:
            i += res-1
            flag = True  # если будет False, то можно завершать проверку. Так как не удовлетворяет условиям
            # переберем все модификации условия
            for mod in self._mods:
                if mod.offset != 0:
                    # по известному смещению
                    pos = i+mod.offset
                    if pos < 0 or pos >= len(words):    # i + pos >= len(words):
                        flag = False
                        break
                    flag_x = False
                    if mod.offset not in used:
                        used += [mod.offset]
                        flag_x = True
                    if not flag_x or _check_condition(words, pos, mod.only_lower, mod.cond) == 0:
                        flag = False
                else:
                    # по неизвестному смещению
                    flag_x = False
                    x = i_start
                    while x < i_end:
                        if x == i or (mod.mode == COND_M_LEFT and x > i) or \
                                     (mod.mode == COND_M_RIGHT and x < i) or (x - i in used):
                            x += 1
                            continue
                        if _check_condition(words, x, mod.only_lower, mod.cond) != 0:
                            used += [x-i]
                            flag_x = True
                            break
                        x += 1
                    if not flag_x:
                        flag = False
                if not flag:
                    break
            if flag:
                return True
        return False

    # проверка условий для выбранного предложения
    def check(self, words, i_start, i_end):
        if self._type == COND_C_ANY:
            for i in range(i_start, i_end):
                if self._check(words, i, i_start, i_end):
                    return True
        else:
            if self._type == COND_C_FIRST:
                # в начале предложения
                pos = i_start
            else:
                # в конце предложения
                pos = i_end - 1
                if pos < i_start:
                    pos = i_start
            if self._check(words, pos, i_start, i_end):
                return True
        return False


# ======== ========= ========= ========= ========= ========= ========= =========
# класс для проверки условий команды
class Condition:
    def __init__(self, q_in_end=COND_Q_NONE, max_sentences=-1):
        self._cond = []
        self._question = q_in_end
        self._max_sentences = max_sentences

    # вернёт позицию нового условия (-1 - не удалось)
    def c(self, cond, c_=COND_C_ANY, only_lower=True):
        if type(cond) is str:
            cond = [cond]
        self.add(C(cond, c_, only_lower))
        return self

    def m(self, cond, offset=0, m_=COND_M_ANY, i=-1, only_lower=True):
        if cond is None and offset == 0:
            print("Модификатор \"Любое слово\" не может быть установлен при смещении равном 0!")
            return self
        if type(cond) is str:
            length = 1
            cond = [cond]
        else:
            length = len(self._cond)
        if length == 0:
            return self
        elif 0 > i >= length:
            i = len(self._cond)-1
        if self._cond[i].is_have_offset(offset):
            print("Модификатор условия содержит кривой offset. Его значение установлено в 0!")
            offset = 0
            m_ = COND_M_ANY
        self._cond[i].set_mod(M(cond, offset, m_, only_lower))
        return self

    # вернёт позицию нового условия (-1 - не удалось)
    def add(self, condition, mods=None):
        _type = condition.get_type()
        # Проверим модификаторы условия
        if mods is not None:
            used_offset = []
            for mod in mods:
                if mod.offset != 0:
                    if mod.offset in used_offset:
                        print("Модификатор условия содержит кривой offset. Его значение установлено в COND_M_ANY!")
                        mod.offset = 0
                        mod.mode = COND_M_ANY
                    else:
                        used_offset += [mod.offset]
                condition.set_mod(mod)
        # Проверим тип условия
        flag = True
        if _type in [-1, 1]:
            for cond in self._cond:
                if cond.get_type() == _type:
                    flag = False
                    print("Такой тип условии уже присутствует. Не установлено!")
                    break
        if flag:
            self._cond += [condition]
            return len(self._cond)-1
        return -1

    # проверка предложении на соотвествие условиям
    def check(self, mp, fn_accessible):
        if mp.sentences is not None:
            i = 0
            for s in mp.sentences:
                # проверим доступность команды при текущих параметрах предложения
                if not (fn_accessible() or i in mp.sentences_ref):
                    continue
                # проверим есть ли в конце знак вопроса
                if self._question != COND_Q_NONE:
                    if '?' in mp.words[s[1]-1][2]:
                        if self._question == COND_Q_NO:
                            continue
                    else:
                        if self._question == COND_Q_YES:
                            continue
                # проверим в каждом предложении условия
                flag = True
                for cond in self._cond:
                    if not cond.check(mp.words, s[0], s[1]):
                        flag = False
                        break
                if flag:
                    mp.current_sentence = s
                    return True
                i += 1
                if i == self._max_sentences:
                    break
        return False
