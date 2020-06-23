import application_data
import core.vainglory.func as _f
import yadisk
import json
import io


def _get():
    return ['б', 'b', 'с', 's', 'з', 'g'], [[0, 109, 218], [327, 436, 545], [654, 763, 872], [981, 1090, 1200],
                                            [1250, 1300, 1350], [1400, 1467, 1533], [1600, 1667, 1733],
                                            [1800, 1867, 1933], [2000, 2134, 2267], [2400, 2600, 2800]]


def _is_rank(string, s, x):
    if not string.isnumeric():
        rank = string[:-1]
        if rank.isnumeric() and string[-1] in s:
            rank = int(rank)
            if 1 <= rank <= 10:
                return x[rank-1][s.index(string[-1]) // 2]
            return -1
        else:
            return -1
    else:
        rank = int(string)
        if rank < 0:
            return -1
        return rank


def analyze(mp):
    if mp.length == 0:
        return True
    if mp.prefix[0] == '!' and mp.words[0][1] in ["rank", "ранг"]:
        j = _load(True)
        msg = ""
        not_found = ""
        res = mp.find_nicknames(is_all=False)
        if len(res) == 0:
            res = {str(mp.uid): mp.ref(True)}
        for n in res:
            if res[n] in j:
                msg += "5x5: " + _f.convert_rank(j[res[n]][0][0]) + " | " + "3x3: " + _f.convert_rank(
                    j[res[n]][0][1]) + " | " + "блиц: " + _f.convert_rank(j[res[n]][0][2]) + " || " + res[n] + '\n'
            else:
                not_found += n + ' '
        flag = (not_found != "")
        if msg == "" or flag:
            if flag:
                msg += "\nНе найдены: " + not_found
            msg += "\nВы не задали свой ранг. Используйте для этого:\n!set rank [pts5x5] [pts3x3] [ptsBlitz]"
        mp.send(msg)
        return False
    elif mp.length >= 2 and mp.words[0][1] == "set" and mp.words[1][1] == "rank":   # set rank 5x5 3x3 blitz
        sr = []
        s, x = _get()
        for i in range(2, mp.length):
            sr += [_is_rank(mp.words[i][1], s, x)]
            if sr[-1] < 0:
                return mp.send("Значение ранга может быть: 1..10!\nПримеры: 10б, 7s, 2416, 5b, 3g, 8г, 9с")
        if len(sr) == 0:
            mp.send("Укажите хотя бы [pts5x5]!\nПримеры: 10б, 7s, 2416, 5b, 3g, 8г, 9с")
            return True
        _save(mp, sr)
        return False
    return True


def _load(is_short=False):
    res = application_data.get()
    path = res["name"] + application_data.version() + '/notes.txt'
    api = yadisk.YaDisk(token=res["token"])
    j = dict()
    if api.check_token():
        string = ""
        if api.exists(path):
            bytes_io = io.BytesIO(b"")
            api.download(path, bytes_io)
            string = bytes_io.getvalue().decode('utf-8', 'backslashreplace')
            bytes_io.close()
        if string != "":
            j = json.loads(string)
    if is_short:
        return j
    return j, path, api


def _save(mp, sr):
    if mp.nick is None:
        mp.send("Ваш ник мне неизвестен!")
        return
    while len(sr) < 3:
        sr += [-1]
    j, path, api = _load()
    if mp.nick[0] not in j:
        j[mp.nick[0]] = [sr, []]
    else:
        j[mp.nick[0]][0] = sr
    bytes_io = io.BytesIO(json.dumps(j).encode())
    api.upload(bytes_io, path, overwrite=True)
    bytes_io.close()


def update_ranks(text):
    import re
    import core.instance
    msg = ""
    s, x = _get()
    i, lines = 0, text.split('\n')
    lines.pop(0)
    while i < len(lines):
        lines[i] = re.findall(r"\w+", lines[i])
        if 1 > len(lines[i]) > 4:
            msg += "\"%s...\" - кол-во слов в этой строке > 4\n" % lines[i][0]
        else:
            j, sr = 1, [-1, -1, -1]
            while j < len(lines[i]):
                sr[j-1] = _is_rank(lines[i][j], s, x)
                if sr[j-1] < 0:
                    msg += "%s - для параметра #%d установлено значение = -1\n" % (lines[i][0], j-1)
                j += 1
            lines[i] = (lines[i][0], sr)
        i += 1
    if len(lines) == 0:
        msg += "Не сохранено"
    else:
        j, path, api = _load()
        for obj in lines:
            if obj[0] not in j:
                if core.instance.app().disk.user_profile(obj[0], "Vainglory").is_exist():
                    j[obj[0]] = [obj[1], []]
                else:
                    msg += "%s - игрок не найден\n" % obj[0]
            else:
                j[obj[0]][0] = obj[1]
        bytes_io = io.BytesIO(json.dumps(j).encode())
        api.upload(bytes_io, path, overwrite=True)
        bytes_io.close()
    return msg




