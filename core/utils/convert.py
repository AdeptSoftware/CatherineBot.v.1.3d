# 16.11.2018 Преобразование данных из одних в другие
# использует: api_vk_thread.py!


def obj2str(e):
    if type(e) is str:
        return '"'+e+'"'
    elif type(e) is int or type(e) is float:
        return str(e)+''
    elif type(e) is dict:
        return '{'+dict2str(e, False)+'}'
    elif type(e) is list:
        return '['+list2str(e)+']'
    return str(e)


def dict2str(_dict, newline=True):
    if _dict is None:
        return ""
    msg = ""
    for n in _dict:
        msg += '\"'+str(n) + '": ' + obj2str(_dict[n])
        if newline:
            msg += '\n'
        else:
            msg += ' '
    return msg[:len(msg)-2]


def list2str(_list):
    if _list is None:
        return ""
    msg = ""
    for i in _list:
        msg += obj2str(i)+' '
    return msg[:len(msg)-2]
