# 07.02.2019
import core.request.objects.request_thread as _rt
from core.cmd.handlers.common import *
from core.instance import *
from core.utils.fnstr import print_time
import core.utils.is_
import time
import re

from core.strings import std_catherine_refs

import core.rank_system.rs

def h_search(mp):
    if len(mp.fwd) != 1:
        return FN_CONTINUE
    if mp.uid not in [481403141, 9752245]:
        ans = mp.node.get_answers()
        app().vk.send(mp.pid, ans[random.randint(0, len(ans)-1)])
        return FN_BREAK
    user = app().disk.user_profile(mp.fwd[0]["from_id"])
    domain = user.domain()
    msg = "Пользователь не оставлял записей в знакомствах!"
    if domain is not None:
        from core.request.vk_loader import find_comments
        comments = find_comments(domain, 0, mp.prefix[0] == '!') # 898
        if len(comments) != 0:
            msg = "\n\n".join(comments)
            msg = "Найдены записи (" + user.full_name() + "):\n\n" + msg
    app().vk.send(mp.pid, msg)
    return FN_BREAK

def h_search_joke(mp):
    if mp.length != 2:
        return FN_CONTINUE
    import urllib.request
    param = ""
    for byte in mp.words[1][1].encode("cp1251"):
        param += "%"+hex(byte)[2:]
    res = urllib.request.urlopen('http://www.korova.ru/humor/cyborg.php?acronym='+param)
    msg = "Будьте осторожны \"" + mp.words[1][0] + "\" неизвестный науке киборг!"
    if res.getcode() == 200:
        res = re.findall(r"<p>(.*)</p>\r\n<form action", res.read().decode("cp1251"))
        if res is not None and len(res) == 1 and res[0][:10] != "ВАСЯПУПКИН":
            msg = res[0]
    app().vk.send(mp.pid, msg)
    return FN_BREAK

# OnFindPlayer
def h_find_player(mp):
    if mp.length == 2 and mp.words[1][1] == "меня":
        res, unk = {mp.uid: mp.nick}, []
    else:
        res, unk = mp.find_nicknames(unk=True)
    if mp.group == "Vainglory" and len(res) + len(unk) != mp.length+len(mp.fwd)-1:
        return FN_CONTINUE
    # сформируем сообщение
    is_other_group = False  # были переданы сообщения других сообществ
    is_self = False         # меня искали?
    nf, att = 0, []
    msg, not_found, end_message, probably_nickname = "", "", "", ""
    for user_id in res:
        if user_id > 0:
            if res[user_id] is None:
                not_found += "[id" + str(user_id) + "|?] "
                continue
            player_nick = ""
            for nick in res[user_id]:
                player_nick += '||' + nick
            msg += "[id" + str(user_id) + '|' + player_nick[2:] + "] "
            userdata = app().disk.get_userdata(str(user_id))
            if userdata is not None:
                att += userdata[0]
                if userdata[1] is not None:
                    end_message = '\n' + userdata[1] + "\n"
        else:
            if user_id == app().vk.id():
                is_self = True
            else:
                is_other_group = True
    # переберем все слова и попытаемся найти ник
    for obj in unk:
        if type(obj) is int and mp.group == "Vainglory":
            not_found += "@id" + str(obj) + ' '
        else:
            ret = app().disk.possible_nick(obj, mp.group)
            if ret is not None:
                if len(ret) == 1:
                    probably_nickname += "{0}. {1} → {2} vk.com/id{3}\n".format(nf+1, obj, ret[0][0], ret[0][1])
                else:
                    count = 1
                    probably_nickname += "{0}. {1}:\n".format(nf+1, obj)
                    for r in ret:
                        probably_nickname += "→ {0} vk.com/id{1}\n".format(r[0], r[1])
                        count += 1
                        if count >= 3:
                            break
                nf += 1
            elif mp.group != "Vainglory":
                not_found += obj + '\n'
    if msg == "" and not_found == "" and probably_nickname == "" and not is_other_group and not is_self:
        return FN_CONTINUE
    if msg != "":
        msg = "Вы искали: " + msg + '\n'
    if probably_nickname != "":
        probably_nickname = "Может быть, Вы искали:\n" + probably_nickname + '\n'
    if not_found != "":
        not_found = "Не найдены:\n" + not_found + '\n'
    if is_other_group:
        end_message += "Сообщения от других сообществ не анализируются!\n"
    if is_self:
        if is_other_group:
            end_message += "Да и... "
        end_message += "Зачем меня искать? Я же тут почти всегда..."
    return mp.send(msg+probably_nickname+not_found+end_message, att)


# ======== ========= ========= ========= ========= ========= ========= =========
# ======== ========= ========= ========= ========= ========= ========= =========
# ======== ========= ========= ========= ========= ========= ========= =========


# OnHit
def h_hit(mp):
    if mp.node.__name__ == 1:
        if mp.length == 2:
            if mp.words[1][1] in ["все", "всех", "себя"]+std_catherine_refs():
                return mp.send("Может лучше уж тебя шлёпнуть?")
            elif mp.words[1][1] == "меня":
                return mp.send("Вы отшлёпаны! Приятного дня)))")
            else:
                return mp.send((mp.node.get_rnd_answer()).format(mp.transform(mp.words[1][0])))
        res = mp.find_nicknames()
        if len(res) == 1:
            user_id = list(res.keys())[0]
            if user_id > 0 and len(res[user_id]) != 0:
                msg = mp.node.get_rnd_answer()
                if not mp.is_man == 1:
                    msg = msg.replace("отшлёпан", "отшлёпана")
                mp.send(msg.format(res[user_id][0]))
            else:
                return mp.send("Очень смешно...")
        else:
            return mp.send("Может определишься уже кого шлёпнуть?!")
    else:
        return FN_BREAK_STD
    return FN_CONTINUE


# OnCalc
def h_calc(mp):
    symbols = ['+', '-', '*', '/', '^', '%', '÷', ':']
    chars = ['x', 'х', '×']
    flag = False
    for obj in mp.words:
        if obj[2] != "":
            for sym in symbols:
                if sym in obj[2]:
                    flag = True
                    break
        if not flag and obj[1] != "":
            for char in chars:
                if char in obj[1]:
                    flag = True
                    break
        if flag:
            import core.cmd.unique.calculator as _calc
            msg = ""
            res = _calc.main(mp.item["text"])
            if res is not None:
                for r in res:
                    try:
                        if r["result"][0] != '!':
                            msg += r["formula"] + '=' + r["result"] + '   '
                    except Exception as err:
                        app().log(str(err) + '\n' + mp.item["text"])
                if msg != "":
                    mp.send(msg)
                return FN_BREAK
    return FN_CONTINUE


# OnWho
def h_is_locked(mp):
    info = app().get_last_cmd_info(mp.pid, mp.uid, True)
    if info is not None and "last_update" in info:
        if time.time() - info["last_update"] <= 10:
            return FN_BREAK_STD
    return FN_CONTINUE


# OnAchievements
def h_achievements(mp):
    user = mp.find_nicknames(count=1, is_all=False)
    _all = mp.words[0][2] == '+'
    if len(user) != 0:
        _id = list(user.keys())[0]
        msg = user[_id]
    elif mp.length == 1:
        _id = mp.uid
        msg = mp.ref(True)
    else:
        return FN_CONTINUE
    if _id <= 0:
        return FN_CONTINUE
    s = app().disk.s_get(_id)
    # Выведем информацию по рангу
    if _all:
        msg += ": %s (%d ранг: %d/%d)\n" % (core.rank_system.rs.rank_list[s["rank"]][0], s["rank"], s["word"][0],
                                            core.rank_system.rs.rank_list[s["rank"] + 1][1])
    else:
        msg += ": %s (%d ранг)\n" % (core.rank_system.rs.rank_list[s["rank"]][0], s["rank"])
    if _all and s["last"][2] != 0 and mp.item["date"] - s["last"][2] >= 5:
        msg += "Последняя замеченная активность: %s назад\n" % print_time(mp.item["date"]-s["last"][2], True)
    msg_a = ""
    i, count = 0, 0
    for a in s["achievements"]:
        if type(s["achievements"][a]) is int:
            res = core.rank_system.rs.print_achievement(mp, int(a), s["achievements"][a], _all)
        else:
            res = core.rank_system.rs.print_achievement(mp, int(a), s["achievements"][a][int(_all)], _all)
        if res != "":
            count += 1
            if _all or i < 4:
                msg_a += res
                i += 1
    if not _all and i < count:
        msg_a += "Скрыто достижений: %d\n" % (count - i)
    if msg_a != "":
        msg += "\n[Достижения]\n" + msg_a + '\n'
    return mp.send(msg)