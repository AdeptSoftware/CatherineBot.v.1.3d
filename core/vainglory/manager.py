# 10.02.2019
from core.request.objects.req_vainglory import *
import core.basethread
from core.instance import *
import threading
import random
import time


class VaingloryManager(core.basethread.Thread):
    def __init__(self):
        super().__init__("Request", app().disk.get("updates", "request"))
        self._queue = {"Vainglory": []}
        self._lock = threading.RLock()      # блочим данные
        # для Vainglory
        self._vg_max_rpm = 10               # максимальное кол-во запросов в минуту
        self._vg_rpm = 10                   # текущее кол-во возможных запросов
        self._vg_last_update = None

    # формирование запроса
    def request(self, peer_id, profile_list, server, _type, nick_list):
        # рассортируем (добавление происходит одной схожести запросы)
        r = None
        data = []
        flag = False
        for key in profile_list:
            if key != "nick":
                if key > 0:
                    if profile_list[key][1] is not None:
                        if r is None or not r.is_similar(peer_id, server, _type):
                            r = VGRequest(peer_id, [], server, _type)
                        r.add([profile_list[key][1]])
                        if r not in data:
                            data += [r]
                    else:
                        app().log("Ошибочка вышла", profile_list)
                else:
                    if key == app().vk.id():
                        _send_fake(peer_id, _type)
                    else:
                        flag = True
            else:
                while len(profile_list["nick"]) != 0:
                    if r is None or not r.is_similar(peer_id, server, _type):
                        r = VGRequest(peer_id, [], server, _type)
                    r.add(profile_list["nick"])
                    if r not in data:
                        data += [r]
        if flag:
            app().vk.send(peer_id,  "Простите, но сообщения от сообществ не анализирую!")
        if len(data) == 0:
            return
        # отсортировать по порядку
        for d in data:
            d.sorted(nick_list)
        try:
            self._lock.acquire()
            self._queue["Vainglory"] += data
        finally:
            self._lock.release()

    # установка токена
    def set_token(self, peer_id, token):
        pass

    # обновление очереди
    def update(self):
        for _type in self._queue:
            if len(self._queue[_type]) == 0:
                continue
            if _type == "Vainglory":
                self._rpm_update()
                if self._vg_rpm == 0:
                    continue
            # отправим запросы
            while len(self._queue[_type]) != 0:
                try:
                    self._lock.acquire()
                    r = self._queue[_type].pop(0)
                finally:
                    self._lock.release()
                while True:
                    if self._check():
                        r.get()
                        break

    # проверить можно ли отправить запрос
    def _check(self):
        self._rpm_update()  # обновим количество запросов
        if self._vg_rpm != 0:
            self._vg_rpm -= 1
            return True
        return False

    # обновление времени счетчика запросов Vainglory
    def _rpm_update(self):
        if self._vg_last_update is None:
            self._vg_last_update = time.time()
        else:
            if self._vg_rpm >= self._vg_max_rpm:
                return
            now = time.time()
            delta_time = now - self._vg_last_update
            recovery_time = int(60/self._vg_max_rpm)
            recovered_attempts = delta_time // recovery_time
            self._vg_last_update = now - (delta_time-(recovered_attempts*recovery_time))  # now - excess_time
            self._vg_rpm += recovered_attempts
            if self._vg_rpm > self._vg_max_rpm:
                self._vg_rpm = self._vg_max_rpm


# для бота сформировать фейковую информацию по рангу и прочему и отправить е
def _send_fake(peer_id, _type):
    if _type == VG_RANK:
        rb = str(random.randint(2800, 2999))
        r3 = str(random.randint(2600, 2799))
        app().vk.send(peer_id, "блиц: 10з (" + rb + ") | 3x3: 10с (" + r3 + ") | 5x5: 11б (∞) || Catherine")
