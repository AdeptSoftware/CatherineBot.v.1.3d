# 04.02.2019
import time
from core.instance import *
import core.cmd.command
from core.cmd.command_list import get_cmd_list as _gcl


class _UserProfile:
    def __init__(self, node):
        self._data = []                             # элемент self._data состоит из:
        #                                             "node": Node,
        #                                             0: remains_say_count - осталось повторить раз,
        #                                             1: remains_repeat_count - осталось сказать раз
        #                                             "last_update" - время последнего обновления
        self._set(node)

    # не помню как в python называется такого рода передача... буду обзывать передача по "указателю"
    def get(self):
        _list = [[], []]
        for obj in self._data:
            _list[0] += [obj["node"]]
            _list[1] += [[obj[0], obj[1]]]
        return _list

    # установить новый Node
    def _set(self, node):
        s, r = node.get_limit_repeat()
        e = {"node": node, "last_update": time.time(), 0: s, 1: r}
        if e[0] > 0:
            e[0] -= 1
        elif e[1] > 0:
            e[1] -= 1
        self._data += [e]

    # последнее время обновления
    def get_last_element(self):
        e = None
        for d in self._data:
            if e is None or e["last_update"] > d["last_update"]:
                e = d.copy()
        return e

    # запомнить Node, на который мы среагировали
    def remember(self, node):
        for e in self._data:
            if e["node"] == node:
                if e[0] > 0 or e[1] > 0:
                    e["last_update"] = time.time()
                if e[0] > 0:
                    e[0] -= 1
                elif e[1] > 0:
                    e[1] -= 1
                return
        # значит новый Node. Проверим нужно ли удалить старые
        for e in self._data:
            if e["node"].is_child(node) and not e["node"].is_always_remember():
                self._data.remove(e)
                break
        self._set(node)

    # обновление кд текущего Node'а команды
    def update(self, cur_time):
        for_delete = []
        for e in self._data:
            if cur_time - e["last_update"] >= e["node"].get_lifetime():
                flag = False
                l, r = e["node"].get_limit_repeat()
                if l > 0 and e[0] + 1 <= l:
                    e[0] += 1
                    flag = True
                if r > 0 and e[1] + 1 <= r:
                    e[1] = r
                    flag = True
                if flag:
                    e["last_update"] = time.time()
                # если полностью совпадает с данными в node, то надо удалить из списка
                if e[0] == l and e[1] == r:
                    for_delete += [e]
        for e in for_delete:
            self._data.remove(e)
        if len(self._data) == 0:
            return True     # удаляем данный профиль
        return False


class CommandCenter:
    def __init__(self, cmd_list):
        self.is_time_update = False                     # время обновления
        self._cmd = _gcl(cmd_list)                      # список команд
        # в данном диалоге будут заблокированы:
        self._locked_users = {}                         # пользователи (извне/по другой команде)
        self._locked_command = []                       # команды (извне)
        # запомненные пользователи профили (0 - для всех)
        self._memorized_users = {}
        self._used_VIP_command = {}                     # используемые "VIP" команды

    # заблокировать пользователя (НЕ ИСПОЛЬЗУЕТСЯ!)
    # если _time <= 0 - навсегда
    def lock_user(self, user_id, _time):
        if _time > 0:
            self._locked_users[user_id] = time.time() + _time
        else:
            self._locked_users[user_id] = 0

    # заблокировать команду (НЕ ИСПОЛЬЗУЕТСЯ!)
    def lock_cmd(self, cmd_id):
        if cmd_id not in self._locked_command:
            # найдем все команды, используемые на данный момент и уберем их из обращения
            for user_id in self._memorized_users:
                if cmd_id in self._memorized_users[user_id]:
                    self._memorized_users[user_id].pop(cmd_id)
            # внесем в список запрещенных
            self._locked_command += [cmd_id]

    # разблокировать команду (НЕ ИСПОЛЬЗУЕТСЯ!)
    def unlock_cmd(self, cmd_id):
        if cmd_id in self._locked_command:
            self._locked_command.remove(cmd_id)

    # последняя вызванная команда
    def get_last_cmd_info(self, user_id, ignore_common_cmd=False):
        e = None
        if user_id in self._memorized_users:
            e = self._get_last_cmd_info(user_id)
        if not ignore_common_cmd and e is None and 0 in self._memorized_users:
            e = self._get_last_cmd_info(0)
        return e

    # последняя вызванная команда по user_id
    def _get_last_cmd_info(self, user_id):
        e = None
        for cmd_id in self._memorized_users[user_id]:
            last = self._memorized_users[user_id][cmd_id].get_last_element()
            if last is not None and e is None or e["last_update"] > last["last_update"]:
                e = last
        if e is not None:
            return {"node": e["node"], "last_update": e["last_update"]}
        return None

    # обновить список запомненных пользователей
    def update_memorized_users(self, user_id, cmd_id, node):
        if user_id not in self._memorized_users:
            self._memorized_users[user_id] = {cmd_id: _UserProfile(node)}
        else:
            if cmd_id not in self._memorized_users[user_id]:
                self._memorized_users[user_id][cmd_id] = _UserProfile(node)
            else:
                self._memorized_users[user_id][cmd_id].remember(node)

    # запомнить вызов команды
    def remember(self, user_id, cmd_id, node):
        try:
            remember_mode = self._cmd[cmd_id].type()
            if remember_mode != core.cmd.command.CMD_WITHOUT:     # если нужен профиль для команды
                if remember_mode == core.cmd.command.CMD_VIP:     # если имеет тип "команда для одного"
                    if cmd_id in self._used_VIP_command and self._used_VIP_command[cmd_id] != user_id:
                        app().log("Запомнить невозможно команду \""+self._cmd[cmd_id].__name__+"\", т.к. она "
                                  "используется другим пользователем: "+str(self._used_VIP_command[cmd_id]) +
                                  " не "+str(user_id))
                    else:
                        self.update_memorized_users(user_id, cmd_id, node)
                        self._used_VIP_command[cmd_id] = user_id
                else:
                    if remember_mode == core.cmd.command.CMD_ONE_FOR_ALL:
                        user_id = 0
                    self.update_memorized_users(user_id, cmd_id, node)
        except Exception as err:
            app().log(str(err))

    # Вернет True - если список пуст
    @staticmethod
    def _remove(_list, _list_rem):
        length = len(_list_rem)
        if length > 0:
            if len(_list) != length:
                for l in _list_rem:
                    _list.pop(l)
                return len(_list) == 0
            else:
                _list.clear()
                return True
        return False

    # обновление списков
    def update(self):
        #    При 100000 объектах в self._memorized_users время обновления всех данных достигает: 1.4 sec
        #    При 1000 - 0.007 sec
        #    Таким образом, перенос в отдельный поток бессмысленен, т.к. навряд ли в чате будет с ботом общаться
        # одновременно столько участников
        # ======================================
        # пройдемся по запомненным пользователям
        delete_x = []
        cur_time = time.time()
        for user_id in self._memorized_users:
            delete = []
            for cmd_id in self._memorized_users[user_id]:
                if self._memorized_users[user_id][cmd_id].update(cur_time):
                    delete += [cmd_id]
                    if cmd_id in self._used_VIP_command and self._used_VIP_command[cmd_id] == user_id:
                        self._used_VIP_command.pop(cmd_id)
            if self._remove(self._memorized_users[user_id], delete):
                delete_x += [user_id]
        self._remove(self._memorized_users, delete_x)
        # обновим списки заблокированных пользователей
        delete = []
        for user_id in self._locked_users:
            if self._locked_users[user_id] != 0 and cur_time >= self._locked_users[user_id]:
                delete += [user_id]
        self._remove(self._locked_users, delete)
        if self.is_time_update:
            self.is_time_update = False
            print(str(time.time()-cur_time)+" sec.")

    # получить список доступных команд (точнее "указатель" на функцию для анализа и получения ответа)
    def get_available_commands(self, user_id):
        # при 100000 объектах в self._memorized_users время заполнения ret: < 0.01 sec
        if user_id in self._locked_users:
            return []
        ret = {}
        # try: начнем анализ доступных команд
        # вообще должно подготавливаться заранее
        if user_id in self._memorized_users:
            for cmd_id in self._memorized_users[user_id]:
                ret[cmd_id] = self._memorized_users[user_id][cmd_id].get()
                # неиспользованные ноды
                # ret[cmd_id] += self._cmd[cmd_id].get_inactive_root_command(ret[cmd_id])
        if 0 in self._memorized_users:
            for cmd_id in self._memorized_users[0]:
                if cmd_id not in ret:
                    ret[cmd_id] = self._memorized_users[0][cmd_id].get()
        for cmd_id in self._cmd:
            if cmd_id not in ret and cmd_id not in self._locked_command and \
               (cmd_id not in self._used_VIP_command or self._used_VIP_command[cmd_id] == user_id) and \
               self._cmd[cmd_id].is_enable():
                if cmd_id not in ret:
                    ret[cmd_id] = [[self._cmd[cmd_id]], [None]]
        # except:
        return ret
