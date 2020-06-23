import threading


# Ошибки внутри влияют на поток, но не на переменную (acquire и release - вызываются всегда)
# Хотя в целях сохранения правильной работы программы ошибки стоит обрабатывать
# Пример работы
# x = Variable(0)
# ... где-то в потоке:
# with x:
#   x.value += 2
class Variable:
    def __init__(self, value):
        self.value = value
        self._lock = threading.RLock()

    def __enter__(self):
        self._lock.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()


# x = Dictionary()  => аналог: x = {}       # Другими способами не инициализировать
class Dictionary(dict):                     # Прокатит и с list, но не с int и float
    def __init__(self):
        super().__init__()
        self._lock = threading.RLock()

    def __enter__(self):
        self._lock.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()


"""
    # можно какие-нибудь дополнительные функции напихать, но изменение через self[key] = value
    # __setitem__ = можно перехватывать значения, но чутка надо модифицировать:
    def __setitem__(self, key, value):      # вложенные структуры не перехватываются
        if type(value) is dict:
            value = Dictionary() + value.copy()
        super().__setitem__(key, value)

    def __add__(self, other):
        for key in other:
            self[key] = other[key]
        return self


x = Dictionary()
x["12"] = {"1": 10}
x["12"]["1"] = 14
print(x)
"""