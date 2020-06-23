# 28.02.2019
import time
import threading
from core.instance import *
import core.basethread


class Event:
    def __init__(self, name, fn_update, data, next_activate_time=1):
        self.__name__ = name                        # имя события
        self._data = data                           # данные
        self._time = 0                              # время следующего обновления
        self.on_update = fn_update                  # обработка при истечение таймера
        self.set_next_time(next_activate_time)

    def get(self, param, default=None):
        if param in self._data:
            return self._data[param]
        else:
            return default

    def get_time(self):
        return self._time

    # _time - измеряется в секундах (если это 1ый или 2ой случай)
    def set_next_time(self, _time=None):
        _t = time.time()
        if _time is None or _time <= 0:     # 1ый случай
            self._time = _t
        elif _t > _time:                    # 2ой случай
            self._time = _t + _time
        else:
            self._time = _time

    def set(self, param, value):
        if self._data is not None and param in self._data:
            self._data[param] = value
            return True
        else:
            app().log("Event \"" + str(self.__name__) + "\" не содержит " + str(param), self._data, use_print=True)
            return False


class Manager(core.basethread.Thread):
    def __init__(self):
        super().__init__("eventer", 20)                     # обновлять данные ?, сек
        self._event = {}                                    # выполняемые события
        self._lock = threading.RLock()                      # блочим данные

    def new(self, event):
        try:
            self._lock.acquire()
            self._event[event.__name__] = event
        finally:
            self._lock.release()

    # не вызывать в update
    def delete(self, event_name):
        try:
            self._lock.acquire()
            # найдем
            if event_name in self._event:
                self._event.pop(event_name)
            else:
                app().log(event_name + " - неизвестное событие. Удаление невозможно!")
        finally:
            self._lock.release()

    def update(self):
        destroy_list = []
        for name in self._event:
            if time.time() >= self._event[name].get_time():
                if not self._event[name].on_update(self._event[name]):
                    destroy_list += [name]
        if len(destroy_list) != 0:
            for name in destroy_list:
                self._event.pop(name)

    # принудительное обновление не учитывает, а нужно ли удалить данный ивент при выполнении
    def forcibly_update(self, event_name, data=None, update_now=True):
        if event_name in self._event:
            if data is not None:
                for param in data:
                    self._event[event_name].set(param, data[param])
        else:
            app().log("Event с именем \"" + str(event_name) + "\" не существует!", self._event.keys())

    def update_event_data(self, event_name, param, value):
        if event_name in self._event:
            self._event[event_name].set(param, value)
        else:
            app().log("Event с именем \"" + str(event_name) + "\" не существует!", self._event.keys())
