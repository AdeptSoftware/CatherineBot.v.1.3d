# 01.02.2019
# import time
from core.cmd.handlers.common import *
import core.basethread
from core.instance import *
import core.cmd.manager
import core.utils.message_parser
import core.strings

import core.rank_system.rs as rs

import core.cmd.fast_command


class Dialog(core.basethread.Thread):
    def __init__(self, name, peer_id, time_update, cmd):
        super().__init__(name, time_update)
        # инициализация
        self._settings = {"title": name, "pinned": 0}           # настройки чата
        self._peer_id = peer_id                                 # id диалога
        self._q = []                                            # очередь сообщений
        self._manager = core.cmd.manager.CommandCenter(cmd)     # менеджер команд
        self._bot_refs = core.strings.std_catherine_refs()      # обращения
        self._

    # ID текущего диалога
    def id(self, short=False):
        if short:
            c = core.vk.wrapper.get_min_chat_id()
            if self._peer_id >= c:
                return self._peer_id - c
        return self._peer_id

    # добавить в очередь
    def add_to_queue(self, item):
        self._q += [item]

    # получение последнего вызванного Node
    def get_last_cmd_info(self, user_id, ignore_common_cmd=False):
        return self._manager.get_last_cmd_info(user_id, ignore_common_cmd)

    # обновление данных
    def update(self):
        # обработка поступающих сообщений
        if len(self._q) != 0:
            q = self._q.pop(0)
            if "action" in q:
                if "type" in q["action"]:
                    self._on_action(q)
                else:
                    app().log("Action сообщения не валиден!", q["action"])
            self._on_message(q)
        # обновление списка заблокированных команд для пользователей
        self._manager.update()

    # обработка сообщений
    def _on_message(self, item):
        mp = core.utils.message_parser.MessageParser(item, self._bot_refs)
        rs.main(mp)
        if core.cmd.fast_command.analyze(mp):
            return
        _list = self._manager.get_available_commands(mp.uid)
        for cmd_id in _list:
            for i in range(0, len(_list[cmd_id][0])):
                ret = _list[cmd_id][0][i].analyze(mp, _list[cmd_id][1][i], _list=_list[cmd_id][0])
                if ret != FN_CONTINUE:
                    if type(ret) is str:
                        mp.send(ret)
                        self._manager.remember(mp.uid, cmd_id, mp.node)
                    return

    # обработка действий пользователя
    def _on_action(self, item):
        # {"type": "chat_title_update" "text": "R2D3}
        # {'type': 'chat_pin_message', 'member_id': 481403141, 'conversation_message_id': 133, 'message': 'd'}
        # {'type': 'chat_unpin_message', 'member_id': 481403141, 'conversation_message_id': 133}
        # {'type': 'chat_kick_user', 'member_id': 481403141}
        # {'type': 'chat_invite_user', 'member_id': 481403141}
        if item["action"]["type"] == "chat_title_update":
            self._settings["title"] = item["action"]["text"]
        elif item["action"]["type"] == "chat_pin_message":
            self._settings["pinned"] = item["action"]["conversation_message_id"]
        elif item["action"]["type"] == "chat_unpin_message":
            self._settings["pinned"] = 0
        elif item["action"]["type"] == "chat_kick_user":
            if item["from_id"] == item["action"]["member_id"]:
                msg = core.strings.rnd(core.strings.on_leave())

            else:
                msg = core.strings.rnd(core.strings.on_kick())
            app().vk.send(self._peer_id, msg+" [id"+str(item["from_id"])+"|:-(]")
        elif item["action"]["type"] == "chat_invite_user":
            if item["from_id"] == item["action"]["member_id"]:
                app().vk.send(self._peer_id, core.strings.rnd(core.strings.on_repeat_invite()))
            else:
                app().eventer.update_event_data("data_updater", "flag", True)
                app().vk.send(self._peer_id, core.strings.rnd(core.strings.on_invite()))
        else:
            app().log("Новый тип action: " + str(item["action"]["type"]), item["action"])
