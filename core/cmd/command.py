# 06.01.2019
import core.strings
from core.cmd.handlers.common import *


# Константы для Command._type:
CMD_EVERYBODY = 3     # у каждого свой
CMD_ONE_FOR_ALL = 2   # один активный экземляр (на всех)
CMD_VIP = 1           # один активный экземляр (на одного)
CMD_WITHOUT = 0       # без профиля


class Node:
    # h_dict имеет вид: {<on_>: fn}.
    # Дополнительные обработчики [при доб.НОВЫХ надо добавить кроме как в код, еще и в set_handlers!!!]:
    # chk - при проверке (вызов при выполнении списка условий)
    # get - при получении ответа (перед выводом)
    # rpt - при повторе (перед выводом)
    def __init__(self, condition, ans=None, nodes=None, limit=2, repeat=1, lifetime=300, ref=False, h=None, ar=False,
                 name=None):
        self._condition = condition         # список условий
        self._answer = ans                  # список ответов при выполняющемся условии (проверять на None)
        self._nodes = nodes                 # список нодов для продолжения диалога
        self._limit = limit                 # макс. кол-во повторов, сказав нормально (<= 0 - бесконечно)
        self._repeat = repeat               # макс. кол-во повторов, напомнив о сказанном (<= 0 - бесконечно)
        self._lifetime = lifetime           # время жизни пременной после активации
        self._reference = ref               # делать ли обращение к человеку при ответе
        self._always_remember = ar          # запоминать в профиле (не только текущий)

        # дополнительные обработчики
        self._h = None
        if h is not None:
            # проверим содержимое
            flag = True
            for key in h:
                if key not in ["chk", "get", "rpt"]:
                    print("Node.set_handlers(): \""+str(key)+"\" - не существует такого обработчика! Не добавлено!")
                    flag = False
            # инициализируем
            if flag:
                self._h = h
        # установка имени
        if name is not None:
            self.__name__ = name

    # является этот Node в аргументах потомком? (следующим в дереве)
    def is_child(self, node):
        return node in self._nodes

    # нужно ли запоминать этот?
    def is_always_remember(self):
        return self._always_remember

    # нужно ли упоминание?
    def is_ref(self):
        return self._reference

    # время жизни Node
    def get_lifetime(self):
        return self._lifetime

    # получить кол-ва повторов сказанного и повтора из серии "ну ты чего... я же тебе говорила это уже!"
    def get_limit_repeat(self):
        return self._limit, self._repeat

    # получить случайный ответ
    def get_rnd_answer(self):
        if self._answer is not None:
            return core.strings.c_rnd(self._answer, None)
        return FN_CONTINUE

    # получить структуру ответов
    def get_answers(self):
        return self._answer.copy()

    # проверка текста
    def _check(self, mp, fn_accessible):
        if self._condition.check(mp, fn_accessible):
            mp.node = self
            if self._h is not None and "chk" in self._h and self._h["chk"] is not None:
                return self._h["chk"](mp)
            return FN_BREAK_STD
        return FN_CONTINUE

    # получение ответа
    def _get(self, mp, rc, ignore, _list, fn_accessible):
        # rc = None - когда не было еще вызовом команды у текущего пользователя
        if not ignore and rc is not None and self._nodes is not None:
            for node in self._nodes:
                if _list is not None and node not in _list:
                    res = node.analyze(mp, None, True, fn_accessible)
                    if res != FN_CONTINUE:
                        return res
        res = self._check(mp, fn_accessible)
        if res == FN_BREAK_STD:
            # говорим/повторяем
            if rc is None:
                rc = self.get_limit_repeat()
            if rc[0] != 0:
                if not ignore and self._h is not None and "get" in self._h and self._h["get"] is not None:
                    return self._h["get"](mp)
                else:
                    return self.get_rnd_answer()    # говорим
            elif rc[1] != 0:                        # повторяем
                if self._h is not None and "rpt" in self._h and self._h["rpt"] is not None:
                    return core.strings.c_rnd(self._h["rpt"](), None)
                return core.strings.c_rnd(core.strings.std_repeat_list(), None)
        return res

    # проверка и получение ответа (вернет None - если ответа не было получено)
    # ignore - по сути: не проверять self._nodes
    # rsc - remains say count (осталось раз сказать), rrc - r=repeat (повторить)
    # _list - список активных Node'ов для текущей команды
    def analyze(self, mp, rc, ignore=False, fn=None, _list=None):
        if fn is None:
            return self._get(mp, rc, ignore, _list, lambda: True)
        else:
            return self._get(mp, rc, ignore, _list, fn)

    """ == ========= ========= ========= ========= ========= ========= =========
    # Примеры обработчиков
    def h_on_get(ps)
        return res  # string
    def h_on_rpt(ps, rc)
        return ""   # string
    def h_on_chk(ps)
        return True # bool
    ====== ========= ========= ========= ========= ========= ========= ===== """


# вызывается при Node._h["on_rpt"] is None
def _std_repeat(node, rc=None):
    if rc is None:
        rc = node.get_limit_repeat()
    if rc[0] != 0:
        return node.get_rnd_answer()
    elif rc[1] != 0:
        return core.strings.c_rnd(core.strings.std_repeat_list(), None)
    return FN_CONTINUE


class Command:
    def __init__(self, name, nodes, _type=CMD_EVERYBODY, swr=False, enable=True):
        self._start_when_ref = swr
        self._enable = enable               # активно?
        self.__name__ = name                # имя команды
        self._user_nodes = {"all": nodes}   # массив из Node*
        self._type = _type                  # типы поведения

        # * - состав dict: {user_id: [node1, node2, ...], ..., "all": nodes}

    # вернуть тип поведения
    def type(self):
        return self._type

    # доступна ли команда?
    def is_accessible(self):
        return not self._start_when_ref

    # включена ли команда?
    def is_enable(self):
        return self._enable

    # добавить уникальные команды для пользователя
    def add(self, user_id, nodes):
        if user_id in self._user_nodes:
            for node in nodes:
                if node not in self._user_nodes[user_id]:
                    self._user_nodes[user_id] += [node]
        else:
            self._user_nodes[user_id] = nodes
        return self

    # проверить текст, а вдруг это эта команда
    def _check(self, mp, key, rc, _list=None):
        for node in self._user_nodes[key]:
            ret = node.analyze(mp, rc, fn=self.is_accessible, _list=_list)
            if ret != FN_CONTINUE:
                return ret
        return FN_CONTINUE

    # проверим сначала те, которые дб для этого пользователя, а потом общие
    # rc содержит [rsc - remains say count (осталось раз сказать), rrc - r=repeat (повторить)]
    def analyze(self, mp, rc, _list=None):
        if mp.uid in self._user_nodes:
            ret = self._check(mp, mp.uid, rc, _list)
            if ret != FN_CONTINUE:
                return ret
        return self._check(mp, "all", rc, _list)
