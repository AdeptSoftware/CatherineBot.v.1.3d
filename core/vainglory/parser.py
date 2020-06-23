# 16.02.2019
import requests
from core.instance import *
import core.basethread
import core.utils.fnstr
import core.vainglory.func as _f
import core.vainglory.constants as _c
import core.vainglory.database.db_hero as _dbh
import core.vainglory.database.db_talent as _dbt


# главная функция распределения ответов по классу задач
def print_result(peer_id, result, group, _type, params):
    if group == _c.VG_STATS:
        if _type == _c.VG_STATS:
            _print_stats(peer_id, result, params)
        else:
            _print_rank(peer_id, result, params)
    else:
        if _type == _c.VG_RANK:
            _print_rank_extended(peer_id, result, params[0])
        elif _type == _c.VG_50GAMES_DATA:
            _print_matches(peer_id, result, params)
        elif _type == _c.VG_PICK:
            _print_pick_rate(peer_id, result, params)
        elif _type == _c.VG_WIN_RATE:
            _print_win_rate(peer_id, result, params)
        elif _type == _c.VG_TALENTS:
            _print_talent(peer_id, result, params[0])
        else:
            app().log("Неизвестный тип анализа данных: " + str(_type))


def _print_rank(peer_id, res, player_list):
    msg = _f.print_rank_players(res, player_list)
    if len(player_list) != 0:
        msg += "Нет данных: " + core.utils.fnstr.list2str(player_list, ', ')
    app().vk.send(peer_id, msg)


def _print_rank_extended(peer_id, res, nickname):
    try:  # получим данные пользователей
        msg = ""
        data = {}
        skip_count = 0
        matches = _f.get_match_objects(res)
        for match in matches:
            if match.gameMode in ["private_party_blitz_match", "private_party_aral_match", "blitz_pvp_ranked",
                                  "casual_aral"]:
                skip_count += 1
                continue
            flag = False
            for pd in match.players:
                for p in pd:
                    if p.nick == nickname:
                        if msg == "":
                            msg = _f.print_rank(p.nick, p.stats["rankPoints"])
                        # определим тип
                        ret = _dbh.get_hero_role(p.actor)
                        if ret != _dbh.HR_ERROR:
                            if ret not in data:
                                data[ret] = 1
                            else:
                                data[ret] += 1
                        else:
                            app().log("Неизвестный персонаж: " + p.actor)
                        flag = True
                        break
                if flag:
                    break
        if msg != "":
            # подготовим к сортировке
            r = None
            for role in data:
                if r is None or data[r] < data[role]:
                    r = role
            if r is not None and data[r] >= 10:
                msg += "Вероятно, предпочитает играть за " + r + "а (" + str(data[r]) + '/' + _f.game(
                    len(matches) - skip_count) + ')'
            app().vk.send(peer_id, msg)
        else:
            # выведем просто ранг
            if len(matches) != 0:
                for pd in matches[0].players:
                    for p in pd:
                        if p.nick == nickname:
                            app().vk.send(peer_id, _f.print_rank(nickname, p.stats["rankPoints"]))
                            return
            raise RuntimeError("Сервер не вернул необходимых данных!")
    except Exception as err:
        app().log("[Vainglory API]: " + str(err) + '\n' + nickname)
        app().vk.send(peer_id, "К сожалению, не удалось выполнить команду :(")


def _print_stats(peer_id, res, player_list):
    try:
        for data in res["data"]:
            if "guildTag" not in data["attributes"]["stats"]:
                msg = "Игрок " + data["attributes"]["name"] + " играл последний раз в патче " + \
                      data["attributes"]["patchVersion"] + ", а его данные уже не хранятся!"
                app().vk.send(peer_id, msg)
                continue
            tag = ""
            if data["attributes"]["stats"]["guildTag"] != "":
                tag = " [" + data["attributes"]["stats"]["guildTag"] + ']'
            _time = data["attributes"]["createdAt"].replace('Z', ' ', 1).replace('T', ' ', 1).replace('-', '.')
            msg = "Статистика по игроку " + data["attributes"]["name"] + tag + "\n" + \
                  "Обновлено (серв.время): " + _time + "\n" + \
                  "Уровень аккаунта: " + str(data["attributes"]["stats"]["level"]) + "\nRank:\n"
            for p in data["attributes"]["stats"]["rankPoints"]:
                name = _f.convert_stat_name(p)
                msg += "→ " + name + " = " + _f.convert_rank(data["attributes"]["stats"]["rankPoints"][p]) + '\n'
            minute, count = _f.get_hours(data["attributes"]["stats"])
            p = "{:.2f}".format((data["attributes"]["stats"]["wins"]/count)*100)  # % побед
            msg += "\nПроведено часов в игре: {:.1f}".format(minute/60)
            msg += "\nСыграно всего игр: " + str(count) + " (wins: " + str(data["attributes"]["stats"]["wins"]) + \
                   " ★ ~" + str(p) + "%)\n"
            # отсортируем и выведем
            for p in sorted(data["attributes"]["stats"]["gamesPlayed"].items(), key=lambda kv: kv[1], reverse=True):
                if p[0] != "blitz_rounds":
                    msg += "→ " + _f.convert_stat_name(p[0], False) + " = " + str(p[1]) + '\n'
            app().vk.send(peer_id, msg)
    except Exception as err:
        app().log("[Vainglory API]: " + str(err) + '\n' + str(player_list))
        app().vk.send(peer_id, "Не удалось выполнить команду :(")


def _print_matches(peer_id, res, player_list):
    try:
        r_common_gold = 0
        r_common_kills = 0
        r_common_turret = 0
        r_common_kraken = 0
        r_duration_sum = 0
        r_duration = {}
        p_data = {}
        matches = _f.get_match_objects(res)
        for match in matches:
            if match.gameMode not in r_duration:
                r_duration[match.gameMode] = 0
            r_duration[match.gameMode] += match.duration
            r_duration_sum += match.duration
            # начнем анализ
            for roster in match.roster:
                r_common_gold += roster.gold
                r_common_kills += roster.heroKills
                r_common_turret += roster.turretKills
                r_common_kraken += roster.krakenCaptures
            for i in range(0, len(match.players)):
                for p in match.players[i]:
                    if p.nick in player_list:
                        if p.nick not in p_data:
                            p_data[p.nick] = {"turret": 0, "kraken": 0, "kills_jungle": 0, "goldMine": 0,
                                              "crystalMine": 0, "kills": 0, "deaths": 0, "assists": 0, "farm": 0,
                                              "minion_jungle": 0, "minion_line": 0, "obj": p.stats}
                        p_data[p.nick]["turret"] += p.turretCaptures
                        p_data[p.nick]["kraken"] += p.krakenCaptures
                        p_data[p.nick]["goldMine"] += p.goldMineCaptures
                        p_data[p.nick]["crystalMine"] += p.crystalMineCaptures
                        p_data[p.nick]["kills"] += p.kills
                        p_data[p.nick]["deaths"] += p.deaths
                        p_data[p.nick]["assists"] += p.assists
                        p_data[p.nick]["farm"] += p.farm
                        p_data[p.nick]["minion_jungle"] += p.minionKills
                        p_data[p.nick]["minion_line"] += p.nonJungleMinionKills
                        p_data[p.nick]["kills_jungle"] += p.jungleKills
        if len(p_data) != len(player_list):
            raise RuntimeError("Сервер не вернул необходимых данных!")
        # составим сообщение
        msg = _f.title_command(matches, player_list)
        if len(player_list) > 1:
            msg += ". Ранги на момент последней совместной катки: "
        # выведем ранги
        msg += '\n'
        for nick in player_list:
            msg += _f.print_rank(nick, p_data[nick]["obj"]["rankPoints"])
        # выведем информацию по одному игроку pl[0]
        msg += "\nСуммарное время: " + _f.sec2str(r_duration_sum) + " из них:"
        for mode in r_duration:
            msg += "\n• " + _f.convert_stat_name(mode, False) + " (" + _f.sec2str(r_duration[mode]) + ')'
        length = len(matches)
        for pl in player_list:
            # Показатели по игроку
            msg += "\n\nИгроком " + pl + ':'
            msg += _f.print_data("\n• уничтожено турелей: ", p_data, pl, "turret", length)
            msg += _f.print_data("\n• захвачено кракенов: ", p_data, pl, "kraken", length)
            msg += _f.print_data("\n• убийств в лесу (?): ", p_data, pl, "kills_jungle", length)
            msg += _f.print_data("\n• убито лесных монстров: ", p_data, pl, "minion_jungle", length)
            msg += _f.print_data("\n• убито миньонов на линии: ", p_data, pl, "minion_line", length)
            msg += _f.print_data("\n• убит GoldMine (?): ", p_data, pl, "goldMine", length)
            msg += _f.print_data("\n• убит CrystalMine (?): ", p_data, pl, "crystalMine", length)
            msg += _f.print_data("\n• убийства (K): ", p_data, pl, "kills", length)
            msg += _f.print_data("\n• смертей (D): ", p_data, pl, "deaths", length)
            msg += _f.print_data("\n• ассисты (A): ", p_data, pl, "assists", length)
            msg += _f.print_data("\n• farm (?): ", p_data, pl, "farm", length)
        # общая информация
        msg += "\n\nСредние показатели за матч (все игроки (союзные и вражеские))." \
               "\nДлительность/золото на тиму/убийства/турели/кракены и драконы:\n" \
               "{4}/{0}/{1:.2f}/{2}/{3}".format(int((r_common_gold/2)//length), r_common_kills//length,
                                                r_common_turret//length, r_common_kraken//length,
                                                _f.sec2str(r_duration_sum//length))
        app().vk.send(peer_id, msg)
    except Exception as err:
        app().log("[Vainglory API]: " + str(err) + '\n' + str(player_list))
        app().vk.send(peer_id, "Не удалось выполнить команду :(")


def _print_talent(peer_id, res, nickname):
    core.basethread.UnstoppableTask("OnTalent", _talent_task, [peer_id, res, nickname]).execute()


def _talent_task(task_data):
    try:
        talents = {}
        for data in task_data[1]["included"]:
            if data["type"] == "asset":
                result = requests.get(data["attributes"]["URL"])
                if result.status_code == 200:
                    obj = result.json()
                    # т.к. данные отсортированы по времени, то всегда первым идет:
                    # (HeroSelect, HeroSkinSelect), (PlayerFirstSpawn, LevelUp), ..., TalentEquipped, BuyItem,
                    # LearnAbility, и тд
                    actor = None
                    team = "Left"
                    for event in obj:
                        if actor is None:
                            if event["type"] == "HeroSelect" and event["payload"]["Handle"] == task_data[2]:
                                actor = event["payload"]["Hero"]
                                if event["payload"]["Team"] == '2':
                                    team = "Right"
                                continue
                        else:
                            if event["type"] == "TalentEquipped" and event["payload"]["Team"] == team and \
                               event["payload"]["Actor"] == actor and event["payload"]["Talent"] != "NoTalent":
                                if actor in talents:
                                    if event["payload"]["Talent"] not in talents[actor] or \
                                       talents[actor][event["payload"]["Talent"]] < event["payload"]["Level"]:
                                            talents[actor][event["payload"]["Talent"]] = event["payload"]["Level"]
                                else:
                                    talents[actor] = {event["payload"]["Talent"]: event["payload"]["Level"]}
                                break
        if len(talents) == 0:
            app().vk.send(task_data[0], "Игрок " + task_data[2] + " не играл в блицы!")
            return
        # составим сообщение
        vg_hero_data = _dbh.get_hero_data()
        msg = "Игроком " + task_data[2] + " за " + _f.game(len(task_data[1]["data"])) + " использованы таланты:"
        for actor in talents:
            msg += "\n\n"+_dbh.translate(vg_hero_data, actor[1:len(actor)-1], True)+':'
            for talent in talents[actor]:
                msg += "\n• " + _dbt.get_talent_name(talent[1:len(talent)-1]) + ' ' + str(talents[actor][talent])+"ур."
        app().vk.send(task_data[0], msg)
    except Exception as err:
        app().log("[Vainglory API]: " + str(err) + '\n' + task_data[2])
        app().vk.send(task_data[0], "Не удалось выполнить команду для " + task_data[2] + " :(")


def _print_pick_rate(peer_id, res, player_list):
    try:
        pick = {}
        heroes = []
        matches = _f.get_match_objects(res)
        vg_hero_data = _dbh.get_hero_data()
        for match in matches:
            if match.gameMode not in pick:
                pick[match.gameMode] = {}
            flag = False
            for i in range(0, len(match.players)):
                for p in match.players[i]:
                    if p.nick in player_list[0]:
                        if len(heroes) == 0 or heroes[len(heroes)-1][0] != p.actor:
                            heroes += [[p.actor, 1]]
                        else:
                            heroes[len(heroes)-1][1] += 1
                        if p.actor not in pick[match.gameMode]:
                            pick[match.gameMode][p.actor] = [0, 0]
                        if p.winner:
                            pick[match.gameMode][p.actor][0] += 1
                        pick[match.gameMode][p.actor][1] += 1
                        # выйдем
                        flag = True
                        break
                if flag:
                    break
        if len(pick) == 0:
            raise RuntimeError("Сервер не вернул необходимых данных!!!")
        # составим сообщение
        _strings = []
        for mode in pick:
            if mode == "casual_aral":
                continue
            msg_z = _f.convert_stat_name(mode, False)
            if mode in ["casual", "5v5_pvp_casual"]:
                msg_z = "кэж " + msg_z
            msg_z = '['+msg_z+"]:"
            # подготовим данные
            for actor in pick[mode]:
                c = pick[mode][actor][1]/len(matches)*(pick[mode][actor][0]/len(matches))
                pick[mode][actor] = [c, (pick[mode][actor][0]/pick[mode][actor][1])*100, pick[mode][actor][1]]
            hero_picked = sorted(pick[mode].items(), key=lambda kv: kv[1], reverse=True)
            msg_a = ""
            msg_b = ""
            count = 0
            for obj in hero_picked:
                if count > 5 or obj[1][2] <= 3 or mode == "blitz_pvp_ranked":
                    msg_a += _dbh.translate(vg_hero_data, obj[0], True) + ", "
                else:
                    count += 1
                    msg_b += "\n• " + _dbh.translate(vg_hero_data, obj[0], True) + \
                             " ({:.2f}".format(obj[1][1]) + "%, " + _f.game(obj[1][2]) + ")"
            if msg_b == "":
                if msg_a != "":
                    msg_z += " " + msg_a[:len(msg_a)-2]
            else:
                msg_z += msg_b
                if msg_a != "":
                    msg_z += "\n• " + msg_a[:len(msg_a)-2]
            _strings += [msg_z]
        # отсортируем и выведем информацию:
        msg = "Информация по игроку " + player_list[0]+":\n"
        for string in _strings:
            if '\n' in string:
                msg += string + '\n\n'
        for string in _strings:
            if '\n' not in string:
                msg += string + '\n'
        msg += "\n\n[Все режимы]:\n• Последний выбранный герой: " + _dbh.translate(vg_hero_data, heroes[0][0], True) + \
               " (" + _f.game(heroes[0][1]) + " подряд)"
        hero_picked = sorted(heroes, key=lambda kv: kv[1], reverse=True)
        msg_a = ""
        count = 0
        hero_list = []
        for obj in hero_picked:
            if obj[1] > 3 and obj[0] not in hero_list:
                hero_list += [obj[0]]
                msg_a += "\n→ " + _dbh.translate(vg_hero_data, heroes[0][0], True) + " - " + _f.game(obj[1]) + " подряд"
                count += 1
                if count >= 3:
                    break
        if msg_a != "":
            msg += "\n• Из " + _f.game(len(matches)) + " было сыграно на:" + msg_a
        app().vk.send(peer_id, msg)
    except Exception as err:
        app().log("[Vainglory API]: " + str(err) + '\n' + str(player_list))
        app().vk.send(peer_id, "Не удалось выполнить команду :(")


def _print_win_rate(peer_id, res, player_list):
    try:
        matches = _f.get_match_objects(res)
        r_win = {}
        r_count = {}
        r_win_streak = 0
        r_loss_streak = 0
        r_streak = 0
        p_data = {}
        for match in matches:
            if match.gameMode not in r_count:
                r_count[match.gameMode] = 1
                r_win[match.gameMode] = 0
            else:
                r_count[match.gameMode] += 1
            # определим на какой стороне мы (относительно pl[0])
            flag_ally = [False, False]
            for i in range(0, len(match.players)):
                for p in match.players[i]:
                    if p.nick == player_list[0]:
                        flag_ally[i] = True
                        break
            for i in range(0, len(match.players)):
                for p in match.players[i]:
                    if p.nick not in p_data:
                        p_data[p.nick] = {"obj": p.stats}
                        p_data[p.nick][0] = {"wins": 0, "count": 0}
                        p_data[p.nick][1] = {"wins": 0, "count": 0}
                    if p.winner:
                        p_data[p.nick][flag_ally[i]]["wins"] += 1
                        if p.nick == player_list[0]:
                            r_win[match.gameMode] += 1
                            if r_streak >= 0:
                                r_streak += 1
                            else:
                                if r_streak < r_loss_streak:
                                    r_loss_streak = r_streak
                                r_streak = 1
                    else:
                        if p.nick == player_list[0]:
                            if r_streak <= 0:
                                r_streak -= 1
                            else:
                                if r_streak > r_win_streak:
                                    r_win_streak = r_streak
                                r_streak = -1
                    p_data[p.nick][flag_ally[i]]["count"] += 1
        if r_streak > 0 and r_streak > r_win_streak:
            r_win_streak = r_streak
        if r_streak < 0 and r_streak < r_loss_streak:
            r_loss_streak = r_streak
        # проверим все ли игроки есть в p_data:
        for pl in player_list:
            if pl not in p_data:
                raise RuntimeError("Сервер не вернул необходимых данных!")
        # составим сообщение
        msg = _f.title_command(matches, player_list)
        if len(player_list) > 1:
            msg += ". Ранги на момент последней совместной катки: "
        # выведем ранги
        msg += '\n'
        for nick in player_list:
            msg += _f.print_rank(nick, p_data[nick]["obj"]["rankPoints"])
        # винстрик
        msg += "\n\nStreaks: current/win/loss: " + str(r_streak) + '/' + str(r_win_streak) + '/' + \
               str(-r_loss_streak) + '\n'
        # выведем информацию по одному игроку pl[0]
        if len(player_list) == 1:
            msg += "\nПроцент побед " + \
                   _f.percent(p_data[player_list[0]][1]["wins"], p_data[player_list[0]][1]["count"], False)
            for mode in r_win:
                if r_count[mode] == 0:
                    continue
                msg += "\n• " + _f.convert_stat_name(mode, False) + " (" + _f.percent(r_win[mode], r_count[mode]) + ')'
        else:  # выведем информацию по пати
            block1 = ""
            block2 = ""
            for nick in player_list:
                if nick == player_list[0]:
                    continue
                if nick == player_list[0]:
                    continue
                if p_data[nick][0]["count"] != 0:
                    block1 += "\n→ " + nick + " (" + _f.percent(p_data[nick][0]["wins"], p_data[nick][0]["count"]) + ')'
                if p_data[nick][1]["count"] != 0:
                    block2 += "\n→ " + nick + " (" + \
                              _f.percent(p_data[nick][1]["wins"], p_data[nick][1]["count"]) + ')'
            if block2 != "":
                block2 = "• совместно с этим игроком % побед:" + block2
            if block1 != "":
                block1 = "\n• против этого игрока % проигрышей:" + block1
            msg += "\n" + player_list[0] + " сыграл(а):\n" + block2 + block1 + '\n'
        # процент пробед с рандомами
        p_rate = {}
        for nick in p_data:
            if nick not in player_list and p_data[nick][1]["count"] > 1 and p_data[nick][1]["wins"] != 0:
                c = (p_data[nick][1]["count"]/len(matches))*(p_data[nick][1]["wins"]/len(matches))
                p_rate[nick] = [c, p_data[nick][1]["wins"]/p_data[nick][1]["count"], p_data[nick][1]["count"]]
        # найдем троих самых продуктивных для этого процент побед
        if len(p_rate) > 0:
            msg += "\n\nЛучшие игроки, с которыми довелось cыграть в одной тиме:"
            streak = 0  # используем для других нужд
            for p in sorted(p_rate.items(), key=lambda kv: kv[1], reverse=True):
                msg += "\n• " + p[0] + " ({:.2f}%, ".format(p[1][1] * 100) + _f.game(p[1][2]) + ')'
                streak += 1
                if streak == 3:
                    break
        app().vk.send(peer_id, msg)
    except Exception as err:
        app().log("[Vainglory API]: " + str(err) + '\n' + str(player_list))
        app().vk.send(peer_id, "Не удалось выполнить команду :(")
