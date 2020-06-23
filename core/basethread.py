# 13.11.2018 Базовый класс для потоков
import time
import threading
from core.instance import *


# получить только доступ к содержимого этого класса для этого потока!
class Thread:
    # комфортное значение для time_update > 0.5 (чем больше число тем чаще вызываются другие потоки)
    # большой time_update - дольше выход из программы
    def __init__(self, name, time_update=1, sa_we=True):
        self.__name__ = name
        if time_update > 0.5:
            self._time_update = time_update                 # Примерное время обновления
        else:
            self._time_update = 0.5
        self._exit = False
        self._stop_app_when_exit = sa_we
        self._thread = None

    # обновление данных
    def update(self):
        pass

    # запустить поток
    def start(self):
        try:
            if self._thread is None or not self._thread.is_alive():
                self._exit = False
                self._thread = threading.Thread(target=self._run, name=self.__name__)
                self._thread.start()
                return True
        except Exception as err:
            app().log(str(err))
        # неудачно... выходим
        self._exit = True
        return False

    # вырубить поток
    def stop(self):
        self._exit = True

    # цикл потока
    def _run(self):
        while not self._exit:
            try:
                self.update()
            except Exception as err:
                app().log("Возникло исключение в "+str(self.__name__)+".run(): "+str(err))
            time.sleep(self._time_update)
        if self._stop_app_when_exit:
            app().log("Поток [" + str(self.__name__) + "] завершен!", self._exit)
            app().exit()


class UnstoppableTask:
    def __init__(self, name, fn_update, data=None):
        self._data = data
        self.__name__ = name
        self._update = fn_update
        self._thread = None

    # запустить поток
    def execute(self):
        try:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._run, name=self.__name__)
                self._thread.start()
                return True
        except Exception as err:
            app().log(str(err))
        return False

    def _run(self):
        try:
            self._update(self._data)
        except Exception as err:
            app().log("Возникло исключение в " + str(self.__name__) + ".run(): " + str(err))
