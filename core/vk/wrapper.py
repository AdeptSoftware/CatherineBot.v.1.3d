# 19.01.2019
import vk_api
import core.utils.convert
from core.instance import *
import core.basethread
import threading

from vk_api.bot_longpoll import VkBotLongPoll


def get_min_chat_id():
    return 2000000000


class Wrapper(core.basethread.Thread):
    def __init__(self):
        super().__init__("vk", app().disk.get("updates", "vk", 0.5))
        self._api = None
        self._pts = None                    # посл.события, начиная с которого нужно получать данные
        self._lp = None                     # long poll
        self._id = None
        self._c_att = 8

        self._queue = []                    # очередь сообщений
        self._lock = threading.RLock()      # блочим данные

    # вызов метода
    def call(self, method, params):
        try:
            return self._api.method(method, params)
        except Exception as err:
            app().log(translate_error(err, method, params))
            return None

    def console(self, text, queue_ignore=True):
        if queue_ignore:
            self.call("messages.send", {"message": text, "peer_id": app().disk.get("app", "admin_id"), "random_id": 0})
        else:
            self.send(app().disk.get("app", "admin_id"), text)

    def get_long_poll(self):
        return self._lp

    def create(self, token, group_id):
        self._id = group_id
        self._api = vk_api.VkApi(token=token)
        self._lp = VkBotLongPoll(self._api, -1*group_id, 120)
        return True

    def stop(self):
        self._exit = True
        try:
            self._lock.acquire()
            self._queue.clear()
        finally:
            self._lock.release()

    def update(self):
        if len(self._queue) != 0:
            q = self._queue.pop(0)
            self._api.method("messages.send", {"message": q[1], "peer_id": q[0], "attachment": q[2], "random_id": 0})

    def id(self):
        return self._id

    def send(self, peer_id, text, attachment=None, do_not_parse_links=True):
        if text is None or (text == "" and (attachment is None or len(attachment) == 0)):
            return
        if not self._exit:
            self._call_send(peer_id, text, attachment)
        else:
            try:
                self._lock.acquire()
                self._on_message(peer_id, text, attachment, do_not_parse_links)
            finally:
                self._lock.release()

    def _call_send(self, peer_id, text, attachment=None, do_not_parse_links=True):
        att = ""
        if attachment is not None:
            for a in attachment:
                att += ',' + a
            att = att[1:]
        self._api.method("messages.send", {"peer_id": peer_id, "random_id": 0, "message": text, "attachment": att,
                                           "dont_parse_links": do_not_parse_links})

    def _on_message(self, peer_id, text, attachment, do_not_parse_links=True):
        for q in self._queue:
            if q[0] == peer_id and (len(q[1]) + len(text) + 2 < 4096) and (len(attachment) + len(q[2]) <= self._c_att):
                if text not in q[1]:
                    q[1] += "\n\n" + text
                for att in attachment:
                    if att not in q[2]:
                        q[2] += [att]
                return
        if len(text) >= 4096:
            text = text[:4096]
        if len(attachment) > self._c_att:
            attachment = attachment[:8]
        # создаем новое сообщение
        self._queue += [peer_id, text, attachment, do_not_parse_links]


# обработка ошибок (подумать еще над этим)
def translate_error(err, method, params):
    msg = "Method: " + str(method) + "\nParams: " + core.utils.convert.obj2str(params)
    if err is not None:
        if type(err) is str:
            return err
        try:
            code = err.error["error_code"]
            if code == 902:
                msg = str(err.error["error_msg"]) + '\n' + msg
            elif code == 914:
                msg = msg[:200] + '...'
            elif code == 15:
                msg = str(err.error["error_msg"]) + "[id" + str(params["user_id"]) + "|.]" + '\n' + msg
            elif code == 10:    # повторная отправка
                return "Повторная отправка\n" + msg
        except Exception as err:
            return "Ошибка: " + str(err) + '\n' + msg
    return "Ошибка неизвестна!\n" + msg
