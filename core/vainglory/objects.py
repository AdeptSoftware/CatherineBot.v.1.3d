# 14.02.2019
import datetime


class _Roster:
    def __init__(self, roster):
        self.gold = roster["attributes"]["stats"]["gold"]
        self.side = roster["attributes"]["stats"]["side"]
        self.heroKills = roster["attributes"]["stats"]["heroKills"]
        self.turretKills = roster["attributes"]["stats"]["turretKills"]
        self.krakenCaptures = roster["attributes"]["stats"]["krakenCaptures"]
        self.turretsRemaining = roster["attributes"]["stats"]["turretsRemaining"]


class _Player:
    def __init__(self, participant, player):
        self.actor = participant["attributes"]["actor"]
        self.winner = participant["attributes"]["stats"]["winner"]
        self.wentAfk = participant["attributes"]["stats"]["wentAfk"]
        self.turretCaptures = participant["attributes"]["stats"]["turretCaptures"]
        self.skinKey = participant["attributes"]["stats"]["skinKey"]
        self.nonJungleMinionKills = participant["attributes"]["stats"]["nonJungleMinionKills"]
        self.minionKills = participant["attributes"]["stats"]["minionKills"]
        self.krakenCaptures = participant["attributes"]["stats"]["krakenCaptures"]
        self.kills = participant["attributes"]["stats"]["kills"]
        self.jungleKills = participant["attributes"]["stats"]["jungleKills"]
        self.items = participant["attributes"]["stats"]["items"]
        self.itemUses = participant["attributes"]["stats"]["itemUses"]
        self.itemSells = participant["attributes"]["stats"]["itemSells"]
        self.itemGrants = participant["attributes"]["stats"]["itemGrants"]
        self.goldMineCaptures = participant["attributes"]["stats"]["goldMineCaptures"]
        self.gold = participant["attributes"]["stats"]["gold"]
        self.firstAfkTime = participant["attributes"]["stats"]["firstAfkTime"]
        self.farm = participant["attributes"]["stats"]["farm"]
        self.deaths = participant["attributes"]["stats"]["deaths"]
        self.crystalMineCaptures = participant["attributes"]["stats"]["crystalMineCaptures"]
        self.assists = participant["attributes"]["stats"]["assists"]
        self.nick = player["attributes"]["name"]
        self.stats = player["attributes"]["stats"]
        """
        self.gamesPlayed = player["attributes"]["stats"]["gamesPlayed"]
        self.rankPoints = player["attributes"]["stats"]["rankPoints"]
        self.guildTag = player["attributes"]["stats"]["guildTag"]
        self.level = player["attributes"]["stats"]["level"]
        self.xp = player["attributes"]["stats"]["xp"]
        self.wins = player["attributes"]["stats"]["wins"]
        """
        self.actor = self.actor[1:len(self.actor)-1]


class Match:
    def __init__(self, data, roster, participant, player):
        self._createdAt = datetime.datetime.strptime(data["attributes"]["createdAt"], "%Y-%m-%dT%H:%M:%SZ")
        self.duration = data["attributes"]["duration"]
        self.gameMode = data["attributes"]["gameMode"]

        self.roster = []
        self.players = []
        for r_data in data["relationships"]["rosters"]["data"]:
            rd = roster[r_data["id"]]
            self.roster += [_Roster(rd)]
            r = []
            for p_data in rd["relationships"]["participants"]["data"]:
                r += [_Player(participant[p_data["id"]],
                              player[participant[p_data["id"]]["relationships"]["player"]["data"]["id"]])]
            if len(r) != len(rd["relationships"]["participants"]["data"]):
                raise RuntimeError("Возвращен кривой объект!")
            self.players += [r]

    def date(self, fmt="%d.%m"):    # %Y-%m-%dT%H:%M:%SZ
        return self._createdAt.strftime(fmt)
