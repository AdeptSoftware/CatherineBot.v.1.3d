# 06.02.2019
import core.vainglory.database.db_hero as _dbh
import core.mobile_legends.hero as _dbh2
from core.cmd.handlers.common import *      # функции должны возвращать
import core.basethread
import core.strings
import datetime
from core import instance
import random

# OnWhatCharacter
def h_what_character(mp):
    if mp.group is not None:
        if mp.group == "Vainglory":
            mp.send("Играй " + _dbh.rnd_role() + "ом! Хм, может быть, " + _dbh.rnd(True) + " подойдёт...")
        elif mp.group == "MobileLegends":
            heroes = _dbh2.hero()
            index = random.randint(0, len(heroes)-1)
            mp.send(heroes[index] + "?")
    return FN_BREAK


def _probability_answer(mp):
    ans = mp.node.get_answers()
    keys = list(ans.keys())
    probability = []
    frequency = 0
    for key in keys:
        if key != "default":
            probability += [frequency + key]
            frequency += key
    if frequency >= 1:
        if "default" in keys:
            print("Ответы по умолчанию не могут быть выведены, так как частоты групп ответов >= 100%")
        if frequency > 1:
            print("Частоты групп ответов в сумме дали > 100%. Значения будут нормализованы!")
            for i in range(0, len(probability)):
                probability[i] = probability[i]/frequency
    # начнем вывод
    rnd = random.randint(1, 100)
    for i in range(0, len(probability)):
        if probability[i]*100 > rnd:
            return mp.send(ans[keys[i]][random.randint(0, len(ans[keys[i]])-1)])
    # выше вероятностей
    if "default" in keys:
        return mp.send(ans["default"][random.randint(0, len(ans["default"])-1)])
    return FN_CONTINUE


# OnRepeatText
def h_repeat_text(mp):
    res = _probability_answer(mp)
    if res == FN_CONTINUE:
        keys = core.strings.cmd_repeat_text_keys()
        for i in range(mp.current_sentence[0], mp.current_sentence[1]):
            if mp.words[i][1] in keys:
                end_pos = mp.current_sentence[1]
                if "\"" in mp.words[i][2] or ":\"" in mp.words[i][2]:
                    for x in range(i+1, mp.length):
                        end_pos = x+1
                        if "\"" in mp.words[x][2]:
                            break
                string = ""
                for x in range(i+1, end_pos):
                    separator = " "
                    if mp.words[x][2] != "" and mp.words[x][2][0] != "\"":
                        if mp.words[x][2][0] == '-':
                            separator += ' '
                        separator = mp.words[x][2][0] + separator
                    string += mp.words[x][0] + separator
                if string != "":
                    res = string
                break
    return mp.send(res)


# OnRepeatText
def h_repeat_cmd(mp):
    user_id = mp.uid
    if len(mp.fwd) > 0:
        user_id = mp.fwd[0]["from_id"]
    info = instance.app().get_last_cmd_info(mp.pid, user_id)
    if info is not None and "node" in info and info["node"] is not None:
        res = info["node"].get_rnd_answer()
        if type(res) is str:
            return mp.send(res)
    return FN_BREAK_STD


# OnRandInt
def h_rand_int(mp):
    return mp.send(str(random.randint(1, 100)))


# OnDateTime
def h_datetime(mp):
    h = instance.app().disk.get("app", "timezone", 4)
    _time = datetime.datetime.now()
    msg = "Серверное время: " + _time.strftime("%d.%m.%Y %H:%M") + '\n'
    _time += datetime.timedelta(hours=h)
    if h >= 0:
        t = "UTC+" + str(h)
    else:
        t = "UTC-" + str(-h)
    return mp.send(msg + "Время в Москве (" + t + "): " + _time.strftime("%d.%m.%Y %H:%M"))


# OnVariants
def h_or(mp):
    start = mp.current_sentence[0]
    if start+1 < mp.length and start+2 < mp.current_sentence[1]:
        words = [mp.words[start][1], mp.words[start+1][1]]
        if words[0] in ["кто", "что", "че", "чо"] and words[1] in ["лучше", "круче", "выпадет"]:
            start += 2
    ref = ["я"] + core.strings.std_catherine_refs()
    for i in range(0, len(ref)):
        ref[i] = ref[i].lower()
    ans = ["", ""]
    flag = False
    for i in range(start, mp.length):
        if mp.words[i][1] == "или":
            flag = True
        else:
            if mp.words[i][1] in ref:
                ans[flag] += "ты"
            else:
                ans[flag] += mp.words[i][0]
            if mp.words[i][2] != '?':
                ans[flag] += mp.words[i][2]
            ans[flag] += ' '
    return mp.send(ans[random.randint(0, 1)])


# OnWhereIAm
def rnd_pos_on_google_maps(mp):
    if mp.words[0][0] == "где":
        core.basethread.UnstoppableTask("OnWhereIAm", _rnd_gm, mp).execute()
    return FN_BREAK


def _rnd_gm(mp):
    import requests
    import re
    i = 0
    r = None
    res = None
    _r = re.compile(r"null,\[\\\"([^\\]+)\\\"\]\\n")    # old: <meta content=\"([^\"]*)\" property=\"og:description\">
    while i < 1000:
        r = requests.get("https://www.google.com/maps/place/"+_rnd_maps_pos(-56, 78)+','+_rnd_maps_pos(-180, 180) +
                         "?hl=ru")
        if r is not None and r.status_code == 200:
            xx = r.content.decode('utf-8', 'backslashreplace')
            res = _r.findall(xx)
            if res is not None and len(res) != 0:
                result = res[0].lower()
                # print(r.request.url + " " + result)
                skip = False
                for water in ["океан", "море", "залив", "пролив", "озеро", "река", "зал", "sea", "ocean", "проход"]:
                    if water in result:
                        skip = True
                        break
                if not skip:
                    break
        i += 1
    if res is not None and r is not None:
        mp.send(res[0] + "?\n" + r.request.url[8:], do_not_parse_links=False)


def _rnd_maps_pos(min_pos, max_pos, count=6):
    rnd = random.randint(min_pos, max_pos)
    if rnd in [min_pos, max_pos]:
        return str(rnd)
    ret = str(rnd)+'.'
    for i in range(0, count):
        ret += str(random.randint(0, 9))
    return ret


def h_rnd(mp):
    if mp.length == 1:
        return FN_CONTINUE
    iteration = 5
    pos = mp.current_sentence[0]
    if '*' in mp.words[pos][2]:
        pos += 1
        if mp.length == 2:
            return FN_CONTINUE
        iteration = int(mp.words[pos][0])
        if not mp.words[pos][0].isnumeric() or iteration > 100:
            mp.send("После rnd* должно идти число (0 < N <= 100)!")
            return FN_CONTINUE
    if pos+1 < mp.length and mp.words[pos+1][0].isnumeric() and 100 > int(mp.words[pos+1][0]) > 0:
        percent = int(mp.words[pos+1][0])
        if mp.words[pos+1][2] in ['.', ',']:
            mp.send("Вероятность P должна быть целочисленной!")
            return FN_CONTINUE
        if mp.words[pos+1][2] != '%':
            return FN_CONTINUE
    else:
        mp.send("Ожидался ввод вероятности выпадения (0 < P < 100)!")
        return FN_CONTINUE
    # Начнем симуляцию
    msg = ""
    pos = 0
    count = 0
    while pos < iteration:
        rnd = random.randint(1, 100)
        if rnd <= percent:
            if count == 10:
                msg += ",..."
            elif count < 10:
                msg += ", " + str(pos+1)
            count += 1
        pos += 1
    if msg == "":
        mp.send("За " + str(iteration) + " попыток так ничего и не выпало :(")
    else:
        mp.send("Произошло выпадение (раз: " + str(count) + ") на итерациях: " + msg[2:])
    return FN_BREAK

# запуск объявлений
def announcement(e):
    count = e.get("count", 1)
    instance.app().vk.send(e.get("peer_id", 481403141), e.get("msg", "Error!"))
    count -= 1
    if (count <= 0):
<<<<<<< HEAD
        return False
=======
        instance.app().eventer.delete(e.get("name", "Announcement"))
>>>>>>> c97c76809d30453c612ea840c369b44dec63a288
    else:
        e.set("count", count)
        e.set_next_time(e.get("interval", 1))
    return True

def h_announcement(mp):
    if mp.uid not in [481403141, 9752245]:
        return FN_CONTINUE
    if not (mp.length > 3 and mp.words[1][0].isnumeric() and mp.words[2][0].isnumeric()):
        return FN_CONTINUE
    lst = mp.item["text"].split('\n')
    if len(lst) < 2:
        return FN_CONTINUE
    msg = "\n".join(lst[1:])
    interval = int(mp.words[1][0])*60
    name = "Announcement "+str(random.randint(0, 999999))
    instance.app().eventer.new(core.event.eventer.Event(name, announcement, 
                               {"interval": interval, "count": int(mp.words[2][0]), "msg": msg,
                                "peer_id": mp.pid, "name": name}, interval))
    return mp.send(mp.node.get_answers()[0])
