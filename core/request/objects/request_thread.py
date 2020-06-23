# 19.11.2018
from core.instance import *
import threading
import requests


class Request:
    def __init__(self, thread_name, fn_handler, data, url, header=None, params=None):
        self._data = data
        self.__name__ = thread_name
        self._handler = fn_handler
        self._url = url
        self._header = header
        self._params = params
        self._thread = None

    # запустить поток
    def execute(self):
        try:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._call, name=self.__name__)
                self._thread.start()
                return True
        except Exception as err:
            app().log(str(err))
        return False

    def _call(self):
        try:
            self._handler(requests.get(self._url, headers=self._header, params=self._params), self._data)
        except Exception as err:
            app().log("Возникло исключение в " + str(self.__name__) + ".run(): " + str(err))


