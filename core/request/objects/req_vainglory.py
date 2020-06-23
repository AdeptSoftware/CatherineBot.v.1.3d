# 10.02.2019
import core.vainglory.parser as _p
import core.utils.fnstr
from core.instance import *
import requests


# Константы для формирования запроса
VG_RANK = 0
VG_STATS = 1
VG_WIN_RATE = 2
VG_PICK = 3
VG_50GAMES_DATA = 4
VG_TALENTS = 5


_url = "https://api.dc01.gamelockerapp.com/shards/"
_header = {"Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJkNmY5MmE5MC0wZWJhLTAxMzYtODNiOC0wYTU4N"
                            "jQ2MTA1MjgiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNTIxNTg0NDM3LCJwdWIiOiJzZW1jIiwidGl0bGU"
                            "iOiJ2YWluZ2xvcnkiLCJhcHAiOiJhZGVwdHNvZnR3YXJlIiwic2NvcGUiOiJjb21tdW5pdHkiLCJsaW1pdCI6M"
                            "TB9.XyBg3VvfKW1Ae6tGO696nutn1uUvnFmEo-yaNA3v6bg",
           "Accept":        "application/vnd.api+json"}

_limit = 6


class VGRequest:
    # params - это список (для matches - ники (str))
    def __init__(self, peer_id, params, server, _type):
        self.__name__ = "Vainglory"
        self._id = peer_id
        self._server = server.lower()
        self._params = params
        self._type = _type

    def sorted(self, template):
        _list = []
        for t in template:
            if t in self._params:
                _list += [t]
        for p in self._params:
            if p not in _list:
                _list += [p]
        self._params = _list

    def is_similar(self, peer_id, server, _type):
        return self._id == peer_id and self._server == server and len(self._params) < _limit and self._type == _type

    def add(self, params):
        while len(params) != 0 and len(self._params) < _limit:
            p = params.pop(0)
            self._params += [p]

    def get(self):
        if len(self._params) == 0:
            return False
        if (len(self._params) != 1 and self._type == VG_RANK) or self._type == VG_STATS:
            try:
                res = self._method("players", core.utils.fnstr.list2str(self._params, ','))
                if res is not None:
                    if self._type == VG_STATS:
                        _p.on_stats(self._id, res, self._params)
                    else:
                        _p.on_rank(self._id, res, self._params)
                else:
                    return False
            except Exception as err:
                app().log("[Vainglory API]: " + str(err) + '\n' + str(self._params))
                app().vk.send(self._id, "Не удалось выполнить команду :(")
                return False
        else:
            gm = None
            if self._type == VG_TALENTS:
                gm = "blitz_pvp_ranked"
            res = self._method("matches", core.utils.fnstr.list2str(self._params, ','), game_mode=gm)
            if res is None:
                return False
            # if "links" in obj and "next" in obj["links"]: link = obj["links"]["next"]
            if self._type == VG_RANK:
                _p.on_players(self._id, res, self._params, len(self._params) == 1)
            elif self._type == VG_50GAMES_DATA:
                _p.on_matches(self._id, res, self._params)
            elif self._type == VG_PICK:
                _p.on_pick_rate(self._id, res, self._params)
            elif self._type == VG_WIN_RATE:
                _p.on_win_rate(self._id, res, self._params)
            elif self._type == VG_TALENTS:
                _p.on_talent(self._id, res, self._params[0])
            else:
                app().log("Неизвестный тип анализа данных: " + str(self._type))
                return False
        return True

    # game_mode = None - это означает, что любые режимы, а так принимает: "casual,ranked,blitz_pvp_ranked,casual_aral"
    def _method(self, method, players, descending=True, game_mode=None):
        link = _url + self._server + '/' + method + '?' + "filter[playerNames]=" + players
        if method == "matches" and descending:
            link += "&sort=-createdAt"
        if game_mode is not None:
            link += "&filter[gameMode]="+game_mode
        res = requests.get(link, headers=_header)
        if res.status_code == 200:
            return res.json()
        else:
            if res.reason == "Bad Gateway":
                app().vk.send(self._id, "API игры сейчас недоступно!")
            elif res.reason != "Not Found":
                app().log("[Vainglory API]: " + res.reason + '\n' + link)
            else:
                text = "катках"
                if game_mode is not None:
                    text = core.vainglory.func.convert_stat_name(game_mode) + " матчах"
                app().vk.send(self._id, core.utils.fnstr.list2str(self._params, ", ") + " - нет на " +
                              self._server.upper() + " сервере или давно не было в " + text + '!')
            return None
