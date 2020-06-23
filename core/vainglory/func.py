# 16.02.2019
from core.instance import *
import core.utils.fnstr
import core.vainglory.objects


def print_rank_players(res, player_list):
    msg = ""
    for item in res["data"]:
        player_list.remove(item["attributes"]["name"])
        msg += print_rank(item["attributes"]["name"], item["attributes"]["stats"]["rankPoints"])
    return msg


def print_rank(nickname, rank_points, inline=True):
    msg = ""
    for p in rank_points:
        if inline:
            msg += convert_stat_name(p) + ': ' + convert_rank(rank_points[p]) + ' | '
        else:
            msg += "→ " + p + " = " + convert_rank(rank_points) + '\n'
    if inline:
        return msg[:len(msg)-1] + '| ' + nickname + '\n'
    else:
        return "Rank " + nickname + ":\n" + msg


def convert_stat_name(name, is_rank_command=True):
    if name in ["blitz", "blitz_pvp_ranked"]:
        return "блиц"
    elif name == "ranked":
        if is_rank_command:
            return "3x3"
        return "ранг 3x3"
    elif name in ["ranked_5v5", "5v5_pvp_ranked"]:
        if is_rank_command:
            return "5x5"
        return "ранг 5x5"
    elif name in ["aral", "casual_aral"]:
        return "арал"
    elif name == "casual":
        return "3x3"
    elif name in ["casual_5v5", "5v5_pvp_casual"]:
        return "5x5"
    elif name == "private_party_vg_5v5":
        return "частный - 5x5"
    elif name == "private":
        return "частный - 3x3"
    elif name == "private_party_draft_match":
        return "частный - драфт 3х3"
    elif name == "private_party_draft_match_5v5":
        return "частный - драфт 5х5"
    elif name == "private_party_blitz_match":
        return "частный - блиц"
    elif name == "private_party_aral_match":
        return "частный - ARAL"
    else:
        return name


def get_hours(stats):
    minute = 0.0
    count = 0
    for p in stats["gamesPlayed"]:
        count += stats["gamesPlayed"][p]
        if p == "aral":
            minute += 8*stats["gamesPlayed"][p]
        elif p == "blitz":
            minute += 4.5*stats["gamesPlayed"][p]
        elif p == "casual":
            minute += 21*stats["gamesPlayed"][p]
        elif p == "casual_5v5":
            minute += 25*stats["gamesPlayed"][p]
        elif p == "ranked":
            minute += 22*stats["gamesPlayed"][p]
        elif p == "ranked_5v5":
            minute += 26*stats["gamesPlayed"][p]
    return minute, count


# преобразование ранга в привычную форму
def convert_rank(pts):
    _list = [["1б", 0],     ["1с", 109],   ["1з", 218],
             ["2б", 327],   ["2с", 436],   ["2з", 545],
             ["3б", 654],   ["3с", 763],   ["3з", 872],
             ["4б", 981],   ["4с", 1090],  ["4з", 1200],
             ["5б", 1250],  ["5с", 1300],  ["5з", 1350],
             ["6б", 1400],  ["6с", 1467],  ["6з", 1533],
             ["7б", 1600],  ["7с", 1667],  ["7з", 1733],
             ["8б", 1800],  ["8с", 1867],  ["8з", 1933],
             ["9б", 2000],  ["9с", 2134],  ["9з", 2267],
             ["10б", 2400], ["10с", 2600], ["10з", 2800],
             ["∞", 3000]]

    for i in range(1, len(_list)):
        if _list[i-1][1] <= pts < _list[i][1]:
            return _list[i-1][0] + ' ('+str(int(pts))+')'
    if pts < 0:
        return "no rank"
    return str(int(pts))


# составим объекты, по которым будет легче анализировать
def get_match_objects(result):
    player = {}
    roster = {}
    participant = {}
    for data in result["included"]:
        try:
            if data["type"] == "player":
                player[data["id"]] = data
            elif data["type"] == "participant":
                participant[data["id"]] = data
            elif data["type"] == "roster":
                roster[data["id"]] = data
            elif data["type"] == "asset":
                continue
            else:
                app().log("[Vainglory API]: неизвестный тип данных \"" + data["type"] + "\"!", result)
        except Exception as err:
            app().log("[Vainglory API]: " + str(err), data)
    # скомпонуем все что необходимо в кучу
    matches = []
    for data in result["data"]:
        try:
            matches += [core.vainglory.objects.Match(data, roster, participant, player)]
        except Exception as err:
            app().log("[Vainglory API]: " + str(err), data)
    if len(matches) != len(result["data"]):
        return []
    return matches


# ======== ========= ========= ========= ========= ========= ========= =========

def game(count, limit=-1):   # сыграно
    msg = ""
    if 0 < limit <= count:
        msg += "≥ "
    if count != 11 and count % 10 == 1:
        return msg + str(count) + " игра"
    elif count > 14 and count % 10 in [2, 3, 4]:
        return msg + str(count) + " игры"
    else:
        return msg + str(count) + " игр"


def percent(wins, count, _g=True, invert=False):
    if invert:
        if count == 0:
            msg = "100.00%"
        else:
            msg = "{:.2f}%".format(((count-wins)/count)*100)
    else:
        if count == 0:
            msg = "0.00%"
        else:
            msg = "{:.2f}%".format((wins/count)*100)
    if _g:
        return msg + ", " + game(count)
    return msg


def sec2str(seconds):
    res = seconds/3600
    if res < 1:
        return "{:.1f} мин.".format(seconds/60)
    return "{:.1f} ч.".format(res)


def print_data(string, p_data, nick, param, length):
    if p_data[nick][param] == 0:
        return ""
    return string + str(p_data[nick][param]) + " ({:.2f})".format(p_data[nick][param]/length)


# вводная информация
def title_command(matches, player_list):
    length = len(matches)
    if len(player_list) != 1:
        msg = "Игроками " + core.utils.fnstr.list2str(player_list, ', ') + " совместно cыграно " + game(length, 50)
    else:
        msg = "Игроком " + player_list[0] + " cыграно " + game(length, 50)
    if length > 1:
        end = matches[0].date()
        start = matches[length - 1].date()
        if start == end:
            msg += " (" + start + ')'
        else:
            msg += " (" + start + "—" + end + ')'
    else:
        msg += " (" + matches[0].date("%d.%m.%Y") + ")."
    return msg

