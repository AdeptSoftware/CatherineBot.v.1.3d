# 03.05.2019
import core.vainglory.constants as _c
import core.vainglory.parser as _p
from core.instance import *
import core.utils.fnstr
import core.basethread
import threading
import requests
import random
import time


_CONST_MAX_RPM = 10
_CONST_LIMIT = 6


# ======== ========= ========= ========= ========= ========= ========= =========
class _ObjectAPI:
    def __init__(self, token):
        self._token = token
        self._rpm = _CONST_MAX_RPM                  # текущее кол-во доступных запросов
        self._last_update = None                    # последнее обновление

    # отправка запросов
    # game_mode = None - это означает, что любые режимы, а так принимает: "casual,ranked,blitz_pvp_ranked,casual_aral"
    def method(self, peer_id, method, server, param, descending=True, game_mode=None):
        while not self._check():
            time.sleep(1)
        # начнем отправку
        link = "https://api.dc01.gamelockerapp.com/shards/"+server+'/'+method+'?'+"filter[playerNames]="+param
        if method == "matches" and descending:
            link += "&sort=-createdAt"
        if game_mode is not None:
            link += "&filter[gameMode]=" + game_mode
        res = requests.get(link, headers={"Authorization": self._token, "Accept": "application/vnd.api+json"})
        if res.status_code == 200:
            return res.json()
        else:
            if res.reason == "Bad Gateway":
                app().vk.send(peer_id, "API игры сейчас недоступно!")
            elif res.reason != "Not Found":
                app().log("[Vainglory API]: " + res.reason + '\n' + link)
            else:
                text = "катках"
                if game_mode is not None:
                    text = core.vainglory.func.convert_stat_name(game_mode) + " матчах"
                app().vk.send(peer_id, core.utils.fnstr.list2str(param, ", ") + " - нет на " + server.upper() +
                              " сервере или давно не было в " + text + '!')
            return None

    # проверить можно ли отправить запрос
    def _check(self):
        self._refresh()
        if self._rpm != 0:
            self._rpm -= 1
            return True
        return False

    # обновление счетчика доступных запросов
    def _refresh(self):
        if self._last_update is None:
            self._last_update = time.time()
        else:
            if self._rpm >= _CONST_MAX_RPM:
                return
            now = time.time()
            delta_time = now - self._last_update
            recovery_time = int(60/_CONST_MAX_RPM)
            recovered_attempts = delta_time // recovery_time
            self._last_update = now - (delta_time-(recovered_attempts*recovery_time))  # now - excess_time
            self._rpm += recovered_attempts
            if self._rpm > _CONST_MAX_RPM:
                self._rpm = _CONST_MAX_RPM


# ======== ========= ========= ========= ========= ========= ========= =========
class Manager(core.basethread.Thread):
    def __init__(self):
        super().__init__("Request", app().disk.get("updates", "request"))
        self._last = {}                             # последние запросы
        self._objects = {}
        self._lock = threading.RLock()              # блочим данные

    # регистрация токена
    def register_token(self, peer_id, token):
        self._objects[peer_id] = _ObjectAPI(token)

    # формирование запроса
    def make_request(self, peer_id, profile_list, server, _type):
        if peer_id not in self._objects:
            print("Попытка получения запроса от VG API с незарегистрированного чата: " + str(peer_id))
            return
        # создадим список ников, проверим на повтор, проверим на сообщества
        flag = False
        _list = []
        for nick in profile_list["nick"]:
            if nick not in _list:
                _list += [nick]
        for key in profile_list:
            if key != "nick":
                if key > 0:
                    if profile_list[key][1] is not None:
                        if profile_list[key][1] not in _list:
                            _list += [profile_list[key][1]]
                    else:
                        app().vk.send("Ник этого [id" + str(key) + "|игрока] неизвестен!")
                else:
                    if key == app().vk.id():
                        _send_fake(peer_id, _type)
                    else:
                        flag = True
        if flag:
            app().vk.send(peer_id, "Простите, но сообщения от сообществ не анализирую!")
        if len(_list) == 0:
            return
        # проверим, а было ли уже подобное?
        is_exit = False
        group = _group_type(_type, len(_list))
        try:
            self._lock.acquire()
            if server in self._last:
                if group in self._last[server]:
                    if group >= 0:
                        _list_new = []
                        for nick in _list:
                            if nick in self._last[server][group]:
                                self._last[server][group][nick]["last_update"] = time.time()
                                _p.print_result(peer_id, self._last[server][group][nick]["res"], group, _type, [nick])
                                pass
                            else:
                                _list_new += [nick]
                        _list = _list_new
                        _list_new.clear()
                        if len(_list) == 0:
                            is_exit = True
                    else:       # данные собираются для группы игроков, а не для каждого поотдельности
                        for obj in self._last[server][group]:
                            if obj["list"] == _list:
                                is_exit = True
                                obj["last_update"] = time.time()
                                _p.print_result(peer_id, obj["res"], group, _type, _list)
                                break
        finally:
            self._lock.release()
        if not is_exit:
            self._create_task(peer_id, server, _list, group, _type)

    # сохранение полученного ответа
    def save_result(self, result, server, group, param):
        try:    # все что сюда попало - этого точно нет в self._last
            self._lock.acquire()
            if server not in self._last:
                self._last[server] = {}
            if group not in self._last[server]:
                if group >= 0:
                    self._last[server][group] = {}
                else:
                    self._last[server][group] = []
            if group == 1:          # len(param) >= 1
                try:
                    for item in result["data"]:
                        self._last[server][1][item["attributes"]["name"]] = {"res": {"data": [item]},
                                                                             "last_update": time.time()}
                except Exception as err:
                    app().log(str(err))
            elif group >= 0:        # len(param) == 1
                self._last[server][group][param] = {"res": result, "last_update": time.time()}
            else:                   # любой
                self._last[server][group] += [{"res": result, "list": param, "last_update": time.time()}]
        finally:
            self._lock.release()

    # делаем реквест, сохраняем, выводим информацию
    def _create_task(self, peer_id, server, param, group, _type):
        core.basethread.UnstoppableTask("VGRequest", _make_request,
                                        {"manager": self,
                                         "api": self._objects[peer_id],
                                         "group": group,
                                         "type": _type,
                                         "server": server,
                                         "peer_id": peer_id,
                                         "param": param}).execute()


# ======== ========= ========= ========= ========= ========= ========= =========
# получить тип
def _group_type(_type, count):
    if _type == _c.VG_TALENTS:
        return _c.VG_TALENTS
    if (_type == _c.VG_RANK and count > 1) or _type == _c.VG_STATS:
        return _c.VG_STATS
    if _type in [_c.VG_RANK, _c.VG_PICK] or (count == 1 and _type in [_c.VG_WIN_RATE, _c.VG_50GAMES_DATA]):
        return _c.VG_50GAMES_DATA
    return -1


# сделать запрос
def _make_request(data):
    gm = None
    method = "matches"
    p = [data["param"]]
    if data["group"] == _c.VG_STATS:
        method = "players"
        length = len(data["param"])
        if length > _CONST_LIMIT:
            p = []
            pos = 0
            while pos < length:
                p += [data["param"][0+pos:6+pos]]
                pos += 6
    if data["group"] == _c.VG_TALENTS:
        gm = "blitz_pvp_ranked"
    for _list in p:
        try:
            res = data["api"].method(data["peer_id"], method, data["server"],
                                     core.utils.fnstr.list2str(_list, ','), game_mode=gm)
            if res is not None:
                data["manager"].save_result(res, data["server"], data["group"], _list)
                _p.print_result(data["peer_id"], res, data["group"], data["type"], _list)
        except Exception as err:
            app().log("[Vainglory API]: При создании запроса произошла ошибка = " + str(err))


# для бота сформировать фейковую информацию по рангу и прочему и отправить е
def _send_fake(peer_id, _type):
    if _type == _c.VG_RANK:
        rb = str(random.randint(2800, 2999))
        r3 = str(random.randint(2600, 2799))
        app().vk.send(peer_id, "блиц: 10з (" + rb + ") | 3x3: 10с (" + r3 + ") | 5x5: 11б (∞) || Catherine")
