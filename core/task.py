# 14.08.2019 Менеджер задач
import threading
import core.safe
import time


class TaskManager:
    def __init__(self, name="TaskManager", h_error=print):
        self._t = threading.Thread(name=name, target=self._update)
        self._q = core.safe.Variable(dict())
        self._h_error = h_error                 # print при ошибке не завершает процесс
        self._exit = False
        self._t.start()

    def _get(self, key=0):
        with self._q:
            if self._q.value:
                if not key:
                    return self._q.value.pop(self._next())
                return self._q.value.pop(key)
        return None

    def _put(self, item):
        with self._q:
            if item[0] in self._q.value:
                self._q.value[item[0]] += [item[1]]
            else:
                self._q.value[item[0]] = [item[1]]

    def _next(self):
        with self._q:
            if self._q.value:
                return sorted(self._q.value.keys())[0]
        return None

    # cmp должно возвращать результат сравнения (True/False)
    def search(self, cmp, data=None, pop=False):
        with self._q:
            for key in self._q.value:
                for obj in self._q.value[key]:
                    if (data is None and cmp(key, obj)) or (data is not None and cmp(key, obj, data)):
                        try:
                            if pop:
                                self._q.value[key].remove(obj)
                        finally:
                            return [dict(obj[1]), key]

    def append(self, delta, fn, data=None):
        if int(delta) <= 0:
            self._call(fn, data)
        else:
            self._put((int(time.time()+delta), (fn, data)))

    @staticmethod
    def _call(fn, data):
        if data is None:
            fn()
        else:
            fn(data)

    def stop(self):
        self._exit = True

    def _update(self):
        while not self._exit:
            try:
                key = self._next()
                if key is None or key-time.time() > 0:
                    time.sleep(1)
                    continue
                for obj in self._get(key):
                    self._call(obj[0], obj[1])
            except Exception as err:
                if self._h_error(err):
                    return
