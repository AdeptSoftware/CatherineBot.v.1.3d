# 29.09.2019
import core.strings
import core.basethread
import core.cmd.manager
import core.cmd.fast_command
import core.utils.message_parser
from core.cmd.handlers.common import *
from core.instance import *

_refs = core.strings.std_catherine_refs()


class Dialog(core.basethread.Thread):
    def __init__(self, name, setting):
        super().__init__(name, 0.5)
        self._manager = core.cmd.manager.CommandCenter(setting["cmd"])
        self._setting = setting                                 # настройки чата
        self._queue   = []                                      # очередь сообщений

        self._setting["pinned"] = None
        self._setting["title"]  = None

    def add(self, item):
        self._queue += [item]

    def update(self):
        if self._queue:
            item = self._queue.pop(0)
            if "action" in item:
                if "type" in item["action"]:
                    self._on_action(item)
            else:
                self._on_message(item)
        # обновление списка заблокированных команд для пользователей
        self._manager.update()

    def _h(self, mp):
        if self._setting["handler"]:
            for fn in self._setting["handler"]:
                if not fn(mp):
                    return False
        return True

    # обработка сообщений
    def _on_message(self, item):
        mp = core.utils.message_parser.MessageParser(item, _refs, group=self._setting["group"])
        if not self._h(mp):
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
        if item["action"]["type"] == "chat_title_update":       # {"type": "chat_title_update" "text": "R2D3"}
            self._setting["title"] = item["action"]["text"]
        elif item["action"]["type"] == "chat_pin_message":      # {'type': 'chat_pin_message', 'member_id': 481403141, 'conversation_message_id': 133, 'message': 'd'}
            self._setting["pinned"] = item["action"]["conversation_message_id"]
        elif item["action"]["type"] == "chat_unpin_message":    # {'type': 'chat_unpin_message', 'member_id': 481403141, 'conversation_message_id': 133}
            self._setting["pinned"] = 0
        elif item["action"]["type"] == "chat_kick_user":        # {'type': 'chat_kick_user', 'member_id': 481403141}
            if self._setting["in_out"]:
                if item["from_id"] == item["action"]["member_id"]:
                    msg = core.strings.rnd(core.strings.on_leave())
                    if self._setting["id"] in [2000000008, 2000000001]:
                        name = app().disk.user_profile(str(item["from_id"])).full_name()
                        msg += "\nНас покинул: [id"+str(item["from_id"])+"|"+name+"]"
                    app().vk.send(self._setting["id"], msg)
                else:
                    app().vk.send(self._setting["id"], core.strings.rnd(core.strings.on_kick()))
                    
        elif item["action"]["type"] == "chat_invite_user":      # {'type': 'chat_invite_user', 'member_id': 481403141}
            if self._setting["in_out"]:
                if item["from_id"] == item["action"]["member_id"]:
                    app().vk.send(self._setting["id"], core.strings.rnd(core.strings.on_repeat_invite()))
                else:
                    app().eventer.update_event_data("data_updater", "flag", True)
                    app().vk.send(self._setting["id"], core.strings.rnd(core.strings.on_invite()))
        else:
            app().log("Новый тип action: " + str(item["action"]["type"]), item["action"])
