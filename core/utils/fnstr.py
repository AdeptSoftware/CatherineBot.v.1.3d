import time
# Здесь функции для работы со стороками


# рисует нули перед числом
def zeros(_val, _count_num):
    res = ""
    _c = len(str(int(_val)))
    while _c < _count_num:
        res += '0'
        _c += 1
    return res + str(int(_val))


def print_time(sec, hide_seconds=False, unix=False, r=None):
    if r is None:
        r = ["ч ", "м ", "сек"]
    if unix:
        sec -= time.time()
    if sec <= 0:
        return "0"+r[2]
    h = sec//3600
    m = (sec-(h*3600))//60
    s = sec-(m*60)-(h*3600)
    msg = ""
    if h > 0:
        msg += str(int(h)) + r[0]
    if m > 0:
        msg += str(int(m)) + r[1]
    if not (hide_seconds and sec >= 60):
        msg += str(int(s)) + r[2]
    return msg


# лист перевести в строку
def list2str(_list, separator):
    string = ""
    for item in _list:
        string += separator + str(item)
    return string[len(separator):]


# https://habr.com/post/326898/ Алгоритм приблизительного распознавания
def distance(s1, s2):
    d = dict()
    len1 = len(s1)
    len2 = len(s2)
    for i in range(-1, len1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, len2 + 1):
        d[(-1, j)] = j + 1
    for i in range(len1):
        for j in range(len2):
            if s1[i] == s2[j]:
                cost = 0
            else:
                cost = 1
            d[(i, j)] = min(d[(i - 1, j)] + 1,  # deletion
                            d[(i, j - 1)] + 1,  # insertion
                            d[(i - 1, j - 1)] + cost)  # substitution
            if i and j and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                # transposition
                d[(i, j)] = min(d[(i, j)], d[i - 2, j - 2] + cost)
    return d[len1 - 1, len2 - 1]