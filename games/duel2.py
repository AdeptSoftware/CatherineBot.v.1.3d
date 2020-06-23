import time
import random
import datetime
import core.task
import core.safe
from core.instance import *
from core.cmd.handlers.common import *
from core.utils.fnstr import zeros as _z, print_time


"""
# module yadisk_storage.py
    import games.duel2
    # DataStorage:
        def __init__(self, data):
            ...
            self.duel = None
        def init_duel(self, data):
            self.duel = games.duel2.Duel(data[0], data[1])

# module command_list.py
    arr_duel = ["дуэль", "пощечина", "duel", "fight", "на", "получай"]
            Command(name="OnDuel", _type=CMD_WITHOUT, nodes=[
                Node(condition=n(arr_duel, COND_C_FIRST, COND_Q_NO, 1),
                     h={"chk": core.instance.app().disk.duel.h_duel}),
                Node(condition=n("дай", COND_C_FIRST, COND_Q_NO, 1),
                     h={"chk": core.instance.app().disk.duel.h_give}),
                Node(condition=n("измени", COND_C_FIRST, COND_Q_NO, 1),
                     h={"chk": core.instance.app().disk.duel.h_change}),
                Node(condition=n(["стата", "статистика"], COND_C_FIRST, COND_Q_NO, 1),
                     h={"chk": core.instance.app().disk.duel.h_stats}),
                Node(condition=n(["магазин", "лавка", "shop"], COND_C_FIRST, COND_Q_NO, 1),
                     h={"chk": core.instance.app().disk.duel.h_shop})]),
            Command(name="OnDuelAction", _type=CMD_WITHOUT, nodes=[
                Node(condition=n(["готов", "да", "принять"]+arr_duel, COND_C_FIRST, COND_Q_NO, 1),
                     h={"chk": core.instance.app().disk.duel.h_ready}),
                Node(condition=n(["заменить", 'з', "улучшить", 'у'], COND_C_FIRST, COND_Q_NO, 1),
                     h={"chk": core.instance.app().disk.duel.h_item}),
                Node(condition=n(["рейтинг", "откаты", "откат"], COND_C_FIRST, COND_Q_NO, 1),
                     h={"chk": core.instance.app().disk.duel.h_rating}),
                Node(condition=n(["модификации", "моды", "mods"], COND_C_FIRST, COND_Q_NO, 1),
                     h={"chk": core.instance.app().disk.duel.h_mods}),
                Node(condition=n(["о бое", "инфа", "информация"], COND_C_FIRST, COND_Q_NO, 1),
                     h={"chk": core.instance.app().disk.duel.h_tracer}),
                Node(condition=n(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"], COND_C_FIRST, COND_Q_NO, 1),
                     h={"chk": core.instance.app().disk.duel.h_set_mods})]),

# module applicatiion.py
    # перед is_debug:
        self.disk.init_duel(self._disk.duel_data())
    # в admin_console() в save:
        self.vk.console(str(self.disk.duel.s_save()))                     

# module rs.py:
    # в main() после return true в начале:
        core.instance.app().disk.duel.h_check_captcha(mp)
    # в main() после mp.s["last"]:
        if word_count >= 5:
            core.instance.app().disk.duel.preview(mp)
"""


_C, _R, _E, _L, _M = 0, 1, 2, 3, 4
_HP, _DEF, _DMG, _CRT, _CRT_DMG = 0, 1, 2, 3, 4
_HEAD, _MASK, _BODY, _HAND, _FEET, _ITEM, _SHLD = 0, 1, 2, 3, 4, 5, 6


class _DuelManager(core.task.TaskManager):
    def __init__(self):
        super().__init__("DuelManager", self._h_error)
        self.duel_chat          = 2000000004
        self._wait_accept       = 90
        self._wait_action       = 300
        self._wait_cooldown     = 1200

        if app().debug():
            self.duel_chat      = 2000000001
            self._wait_accept   = 60
            self._wait_action   = 60
            self._wait_cooldown = 0

    def _h_error(self, err):
        return app().log("Возникло исключение в " + str(self._t.name) + "._update():" + str(err))

    def cooldown(self):
        cd, t = {}, time.time()
        with self._q:
            for key in self._q.value:
                for obj in self._q.value[key]:
                    if obj[1]["type"] == "duel":
                        _time = key-t
                        for _id in obj[1]["id"]:
                            cd[_id] = _time
        return cd

    def append_duel(self, mp, fn, enemy=None, p_cd=1, is_accepted=False):
        data = {"user_id": mp.uid, "enemy": enemy, "ret": None}
        res = self.search(self._accept, data)
        if res is None and data["ret"] is None:
            username = mp.ref(True)
            if not (enemy is None or username is None):
                if is_accepted:
                    cooldown = self._wait_cooldown
                else:
                    cooldown = self._wait_accept
                self.append(cooldown*p_cd, fn, {"type": "duel", "id": [mp.uid, enemy[0]],
                                                "accepted": is_accepted, "name": [username, enemy[1]]})
            return None
        elif type(data["ret"]) is str:
            mp.send(data["ret"])
            return None
        return res[0]

    def append_mods(self, user_id, mods, fn):
        with self._q:
            for key in self._q.value:
                for obj in self._q.value[key]:
                    if obj[1]["type"] == "mods" and user_id == obj[1]["id"]:
                        obj[1]["mods"] = mods
                        return
        self.append(self._wait_action, fn, {"type": "mods", "id": user_id, "mods": mods})

    def append_item(self, user_id, nickname, slot, item, fn):
        flag = False
        with self._q:
            for key in self._q.value:
                for obj in self._q.value[key]:
                    if obj[1]["type"] == "item" and obj[1]["id"][0] == user_id:
                        obj[0](obj[1])
                        self._q.value[key].remove(obj)
                        flag = True
                        break
                if flag:
                    break
        self.append(self._wait_action, fn, {"type": "item", "id": [user_id, nickname], "slot": slot, "item": item})

    def _accept(self, key, obj, d):                                         # всегда внутри (with self._q)
        if obj[1]["type"] == "duel":
            if d["user_id"] in obj[1]["id"]:
                if obj[1]["accepted"]:                                      # мы в откате
                    if d["enemy"]:
                        d["ret"] = "Вы в откате [%s]" % print_time(key, False, True)
                    else:
                        return False
                elif d["user_id"] == obj[1]["id"][0]:                       # мы пытаемся еще кого-то вызвать на дуэль
                    d["ret"] = "Подождите %s! Хотя бы еще %s!" % (obj[1]["name"][1], print_time(key, unix=True))
                else:                                                       # мы принимаем дуэль
                    if d["enemy"] and d["enemy"][0] not in obj[1]["id"]:
                        d["ret"] = "Вы не приняли вызов от %s (Осталось %s)" % \
                                   (obj[1]["name"][0], print_time(key, unix=True))
                    else:
                        self._q.value[key].remove(obj)
                        return True
            elif d["enemy"] and d["enemy"][0] in obj[1]["id"]:
                if obj[1]["accepted"]:                                  # противник в откате
                    d["ret"] = "%s в откате [%s]" % (d["enemy"][1], print_time(key, unix=True))
                else:                                                   # противник вызван на другую дуэль
                    d["ret"] = "%s ожидает дуэль от %s (Осталось %s)" % \
                                (obj[1]["name"][0], obj[1]["name"][1], print_time(key, unix=True))
            else:                                                       # мы никого не зовем на дуэль
                return False
            return True
        return False


class Duel:
    def __init__(self, api=None, path=None):
        self._pl = core.safe.Dictionary()       # Защищаем _task и эту переменную одновременно
        self._task = _DuelManager()
        self._path = path
        self._api = api
        self._items = {_C: {   # DMG max = HP max / 5;     DEF max = HP max * 0.1;     HP real (max) = HP rare - 15
                       "Шапочка из Фольги":    [_HEAD, _HP,   40],     # +40 хп
                       "Металлический Шлем":   [_HEAD, _DEF,   3],     # +3 к броне
                       "Монокль Тирана":       [_MASK, _CRT,   5],     # 5% шанс на крит
                       "Укрепленный Плащ":     [_BODY, _HP,   30],     # +30 хп
                       "Свинцовый Жакет":      [_BODY, _HP,   35],     # +35 хп
                       "Коса":                 [_HAND, _DMG,   7],     # +7 к урону
                       "Птичья Клетка":        [_HEAD, _HP,   30],     # +30 хп
                       "Тесак":                [_HAND, _DMG,   8],     # +8 к урону
                       "Талисман Охотника":    [_ITEM, _CRT,   4],     # +4% шанс на крит
                       "Терновый Венец":       [_FEET, _DMG,   6],     # +6 к урону
                       "Сабатоны":             [_FEET, _CRT,   5],     # 5% шанс на крит
                       "Килт":                 [_FEET, _HP,   20],     # +20 хп
                       "Дубовое Сердце":       [_ITEM, _HP,   25],     # +25 хп
                       "Набор для Заточки":    [_ITEM, _DMG,   6],     # +6 к урону
                       "Бронзовый Щит":        [_SHLD, _DEF,   4],     # +4 к броне
                       "Деревянный Щит":       [_SHLD, _DEF,   3]},    # +3 к броне
                       _R: {   # Редкие
                       "Сканер":               [_HEAD, _DEF,  -3],     # -3 к броне противника
                       "Кирасирский Шлем":     [_HEAD, _DEF,   7],     # +7 к броне
                       "Маска Самурая":        [_MASK, _CRT,   6],     # +6% шанс на крит
                       "Железный Доспех":      [_BODY, _DEF,   6],     # +6 к броне
                       "Венецианская Маска":   [_MASK, _HP,   50],     # +50 хп
                       "Катана":               [_HAND, _DMG,  10],     # +10 к урону
                       "Моргенштерн":          [_HAND, _DMG,   9],     # +9 к урону
                       "Бронированные Поножи": [_FEET, _DEF,   5],     # +5 к броне
                       "Шапель":               [_HEAD, _DEF,   6],     # +6 к броне
                       "Латная Руковица":      [_HAND, _HP,   45],     # +45 хп
                       "Мистическое Зеркало":  [_SHLD, _DMG,  -5],     # -5 к урону врага
                       "Горнило":              [_ITEM, _HP,   55],     # +55 хп
                       "Револьвер":            [_ITEM, _DMG,  11],     # +11 к урону
                       "Энергощит":            [_SHLD, _HP,   50]},    # +50 хп
                       _E: {   # Эпические
                       "Диадема Концентрации": [_HEAD, _CRT,   9],     # +9% шанс на крит
                       "Маска Друида":         [_MASK, _HP,   50],     # +50 хп
                       "Маска Горгоны":        [_MASK, _HP,  -15],     # -15 хп врага
                       "Демонический Колокол": [_ITEM, _HP,   55],     # +55 хп
                       "Гарпун":               [_SHLD, _CRT,  16],     # +16% шанс на крит
                       "Сервоприводы":         [_FEET, _DMG,  15],     # +15 к урону
                       "Наплечник Атланта":    [_BODY, _DMG,  -4],     # -4 к урону у противника
                       "Экзотическая Броня":   [_BODY, _DEF,   9],     # +9 к броне
                       "Молот Правосудия":     [_HAND, _DMG,  14],     # +14 к урону
                       "Нейроимплант":         [_HEAD, _HP,   60],     # +60 хп
                       "Ураганный Курок":      [_HAND, _CRT,  15],     # +15% шанс на крит
                       "Латные Ноги":          [_FEET, _DEF,   8],     # +8 к броне
                       "Электрозачарование":   [_ITEM, _DMG,  10]},    # +10 к урону
                       _L: {   # Легендарные
                       "Драконий Шлем":        [_HEAD, _DEF,  15],     # +15 к броне
                       "Балаклава Саб-Зиро":   [_MASK, _DEF,  12],     # +12 к броне
                       "Трезубец":             [_SHLD, _DMG,  20],     # +20 к урону
                       "Призрачная Броня":     [_BODY, _DEF,  18],     # +18 к броне
                       "Крылатые Доспехи":     [_BODY, _DEF,  17],     # +17 к броне
                       "Плазменный Резак":     [_HAND, _DMG,  16],     # +16 к урону
                       "Зачарованные Латы":    [_FEET, _HP,   75],     # +75 хп
                       "Разрушитель Миров":    [_HAND, _DMG,  15],     # +15 к урону
                       "Кукла Вуду":           [_ITEM, _HP,  -10],     # -10 хп врага
                       "Экскалибур":           [_HAND, _DMG,  15],     # +15 к урону
                       "Защитная Аура":        [_ITEM, _DEF,  12],     # +12 к броне
                       "Огненная Плеть":       [_HAND, _DMG,  10],     # +10 к урону
                       "Отражающий Блок":      [_SHLD, _DMG, -10]},    # -10 к урону у противника
                       _M: {   # Мифические
                       "Шлем Архангела":       [_HEAD, _HP,   80],     # +80 хп
                       "Глаз Души":            [_ITEM, _HP,   60],     # +60 хп
                       "Маска Атеиста":        [_MASK, _DMG,  10],     # +10 к урону
                       "Броня Хаоса":          [_BODY, _DEF,  20],     # +20 к броне
                       "Дамоклов Меч":         [_HAND, _DEF, -15],     # -15 к броне врага
                       "Бан Хаммер":           [_HAND, _DMG,  20],     # +20 к урону
                       "Дезинтегратор":        [_HAND, _DEF, -12],     # -12 к броне противника
                       "Поножи Валькирии":     [_FEET, _DEF,  15],     # +15 к броне
                       "Спартанский Сапог":    [_FEET, _DMG,  20],     # +20 к урону
                       "Генератор Хаоса":      [_ITEM, _DEF, -10],     # -10 к броне противника
                       "Линза Безумца":        [_ITEM, _CRT,  20],     # +20% шанса на крит
                       "Щит Безумца":          [_SHLD, _CRT, -12]}}    # -12% шанс на крит у противника}
        self._slots  = ["🎩", "🎭", "🥋", "🥊", "👟", "💎", "🛡"]
        self._params = ["❤", "🛡", "💣", "❗", "🔧"]    # 🎲
        self._rare   = ["Об", "Рд", "Эп", "Лг", "Мф"]
        self._act    = ["⇄", "⇧", "🎁", "🔧"]  # 🞇⭳
        self._mods = {"Инстинкт Зверя": ["🐾", "%d уворота от атак", 3],
                      "Вампиризм": ["🦇", "Каждая атака восстанавливает хп в размере %d%% нанесенного урона", 25],
                      "Мьельнир": ["⚡", "%d%% шанс выпустить молнию во врага, наносящую %d%% урона", (40, 150)],
                      "Дыхание Мертвеца": ["❄", "Противник наносит на %d%% меньше урона", 20, _DMG],
                      "Оглушающий Удар": ["💫", "%d%% шанс оглушить врага на %d хода", (18, 2)],
                      "Яд": ["🐉", "Каждая атака отравляет цель по %1.f хп за ход (макс.стаков: %d)", (3.5, 10)],
                      "Инициатор": ["⌛", "Следующий бой начнёте первым", None],
                      "Сытный Обед": ["🍗", "В первый ход ваше здоровье выше на %d ед", 120],
                      "Чёрная Метка": ["💔", "В бою всегда %d хп, %d брони и %d шанс на крит", (40, 0, 50)],
                      "Контрудар": ["🤺", "%d%% шанс ответить на удар", 30],
                      "Подарок": ["🎁", "После боя случайный слот будет улучшен", None],
                      "Антиквар": ["💍", "При проигрыше шанс получить редкий предмет выше на %d%%", 20],
                      "Маховик Времени": ["🕛", "Следующая дуэль откатится на %d%% быстрее", 50],
                      "Акция": ["💲", "Проигравший получает доп.очки ярости: %d шт.", 2],
                      "Фатальная Ошибка": ["💞", "Игроки меняются здоровьем", None],
                      "Духовная Связь": ["🔗", "Весь полученный урон делится на двоих", None],
                      "Закаленная Сталь": ["🚫", "Критический урон врага игнорируется", None],
                      "Амулет Ведьмака": ["📿", "Вражеские эффекты на Вас не действуют", None],
                      "Двойник": ["👥", "Избежание смертельного удара %d раз", 1],
                      "Агония": ["💥", "Урон выше %.1f раза, когда останется меньше %d%% макс.хп", (2.0, 20)],
                      "Дары Смерти": ["💀", "%d%% шанс мгновенно убить цель", 15],
                      "Прорубающее Лезвие": ["🔪", "Броня противника уменьшена на %d%%", 25, _DEF],
                      "Рок Судьбы": ["🔮", "Игроки меняются модификаторами", None],
                      "Армагеддон": ["☄", "Игроки получают 1 раз урон, зависящий от их макс.здоровья (до %d%%)", 50],
                      "Феникс": ["🔥", "%d%% шанс воскреснуть при смерти с %d хп", (40, 50)],
                      "Сердцебиение": ["💓", "Макс.здоровье противника на %d%% ниже", 30, _HP],
                      "Благословение": ["🌄", "Эффекты от модификаторов усиливаются в %d раза", 2],
                      "Эфес": ["🗡", "Каждые %d хода дополнительный удар", 3],
                      "Ручная Сова": ["🦉", "с %d до %d по мск следующая дуэль откатится быстрее на %d%%", (0, 6, 80)],
                      "Щит Хавела": ["🛡", "Ваша защита крепче на %d%%, но урон ниже на %d%%", (20, 5)],
                      "Критический Уровень": ["⚠", "Шанс крита врага снижен на %d%%", 20, _CRT],
                      "Поглощение Жизни": ["💖", "%d%% макс.хп врага становится вашим", 15, _HP],
                      "Воровство": ["🚮", "%d%% урона врага становится вашим", 15, _DMG],
                      "Торнадо": ["🌪", "Каждый ход случайный игрок теряет %d%% макс.хп", 12],
                      "Карма": ["☔", "Ваша броня ниже на %d%%, но коэф.крит.урона выше на %1.f ед", (40, 4)],
                      "Адреналин": ["💉", "Ваш урон на %d ед больше", 17, _DMG],
                      "Крепкий Хребет": ["🐻", "Здоровье увеличено на %d ед", 75, _HP],
                      "Концентрация": ["🧘", "Критический урон выше на %d пунктов", 17, _CRT],
                      "Безумец": ["🗿", "При победе %d%% шанс получить эп.предмет (0 брони)", 18],
                      "Бодрость": ["☕", "%d%% шанс нанести дополнительный %d-кратный урон", (16, 4)],
                      "Точность": ["🎯", "Ваш урон без разброса и выше на %d%%", 15],
                      "Опьянение": ["🍺", "Разброс вашего урона выше [%.1f; %.1f]", (0.7, 1.7)],
                      "Молодильные Яблоки": ["🍏", "Постоянная регенерация %d%% текущего хп за ход", 4],
                      "Элексир": ["🧪", "За каждый потерянный %% макс.здоровья получаете %.1f%% к урону", 0.2],
                      "Увядание": ["🥀", "Противник каждый ход теряете %d%% макс.здоровья", 2],
                      "Запрет": ["⛔", "Случайный модификатор врага игнорируется", None],
                      "Жадность": ["🧤", "Случайный модификатор врага становится вашим", None],
                      "Альфа-Самец": ["🦌", "Даёт метку охоты перед боем", None],
                      "Пацифист": ["☮", "Здоровья больше в %d раза, но атакуете 1 раз в %d хода", (3, 3)],
                      "Геракл": ["🤦", "При поражении шанс получить лег.предмет выше в %d раз (+%d к урону)", (4, 20)],
                      "Нокаут": ["💪", "После %d ходов бездействия вы наносёте %d урона по врагу", (5, 300)],
                      "Скрещенные Пальцы": ["🤞", "Модификаторы, влияющие на ваши статы перед боем игнорируются", None],
                      "Уязвимые Места": ["🔑", "Коэф.крит.урона будет на %1.f больше", 2.5],
                      "Воспламенение": ["🌞", "%d%% шанс поджечь на %d хода, нанося %d урона", (20, 5, 17)],
                      "Ловкость": ["👣", "%d%% шанс увернуться от атак и получить +%d%% шанс на крит", (25, 10)],
                      "Молитва": ["🙏", "Ваша защита выше на %d ед", 14, _DEF],
                      "По Пальцам": ["🔨", "Каждый ход враг получает -%d%% к случайной характеристике на 1 ход", 20],
                      "Четырёхлистник": ["🍀", "В ходе боя может выпасть до %d-х модификаторов с шансом %d%%", (3, 18)],
                      "Призрак": ["👻", "Игроки отвлекаются на призрака, шанс убить которого %d%%. Урон по отвлекшемуся "
                                  "на %d%% выше, а убивший призрака наносит на %d%% больше урона.", (10, 10, 40)],
                      "Коррозия Брони": ["🌁", "Броня врага игнорируется на %d ход", 2],
                      "Забвение": ["💤", "Противник засыпает на %d хода. Может проснуться от удара с шансом в %d%%", (3, 40)],
                      "Очки": ["👓", "В следующем бою %d очка рейтинга превратятся в %d очков ярости", (3, 6)],
                      "Везунчик": ["🎲", "Вы не можете пропустить ход, а ваш коэф.крит.урона выше на %1.f", 2.5],
                      "Заказ": ["🚷", "Победа даст вам доп. +%d к рейтингу", 2],
                      "Неожиданные Атаки": ["💯", "У Вас будет 100%% шанс на крит на %1.f хода", 2],
                      "Болевой Порог": ["📊", "Враг не сможет нанести больше %d урона", 40],
                      "Иглы": ["🦔", "Каждый %d-ый удар критический", 5],
                      "Губка": ["🧽", "Вы впитываете %d%% урона врага и через %d хода враг получит его обратно", (20, 3)],
                      "Защитная Экипировка": ["🥽", "Брони на %d ед больше, но крит.удары снимают по %d ед брони", (15, 3)],
                      "Панцирь": ["🐢", "%d%% шанс получить только %d%% урона", (23, 45)]}
        self._max = (999, 60, 99, 100)
        self._std = (50, 2, 10, 0, 1.5)
        #                   _C   _R   _E   _L   _M
        self._upd = {_HP:   [3,   5,   8,   12,   16],
                     _DEF: [0.2, 0.5, 0.8, 1.2,  1.6],
                     _DMG: [0.5, 0.75, 1,  1.25, 1.5],
                     _CRT: [0.5, 0.9, 1.3, 1.7,   2]}
        self._p_item = ((4, 2.5, 1.3, 0.6), (3.3, 1.7, 0.8, 0.3))
        self._moves = []
        self._last_duel = []
        # Прочее
        self.load_v2()
        self._on_timer_save({"type": "save"}, save=False)

    def __del__(self):
        self._task.stop()
        with self._pl:
            self.save(self._path+'.del.txt')

    # ==== ========= ========= ========= ========= ========= ========= =========

    def load_v1(self, path):
        self._pl.clear()
        if self._api and path:
            v1 = self._api.download(path, False)["stats"]
            for key in v1:
                _id = int(key)
                duel = v1[key]["duel"]              # slots, mods, seasons, wins, streak, count, pts, wrath
                p = self._default({}, [])           # slots,       seasons, wins,         count, pts
                for key2 in duel["slots"]:
                    p["slots"][int(key2)] = duel["slots"][key2]
                p["wins"]  = duel["wins"]
                p["count"] = duel["count"]
                p["pts"]   = duel["pts"]
                if "seasons" in duel:
                    for season in duel["seasons"]:
                        self._season(p, season, 0)
                self._pl[_id] = p
            print("Duel v1 loaded (%s)" % path)

    def load_v2(self):
        self._pl.clear()
        if self._api and self._path:
            v2 = self._api.download(self._path, False)
            if v2:
                for _id in v2:
                    self._pl[int(_id)] = {}
                    for key in v2[_id]:
                        if key == "slots":
                            self._pl[int(_id)][key] = {}
                            for s in v2[_id][key]:
                                self._pl[int(_id)][key][int(s)] = v2[_id][key][s]
                        else:
                            self._pl[int(_id)][key] = v2[_id][key]
                print("Duel loaded (%s)" % self._path)

    def save(self, path=None):      # Используется из вне!
        if not path:
            path = self._path
        if self._pl and not app().debug():
            self._api.upload(path, self._pl, False)
            print("Duel saved to " + path)
            return True
        return False

    def s_save(self):
        with self._pl:
            return self.save()

    def clear(self, clear_seasons=False):
        if clear_seasons:
            self._pl = {}
        else:
            for _id in self._pl:
                self._clear(self._pl[_id], False)
        print("Duel clean")

    def new_season(self, season_name):
        self.save("duel.%s.json" % season_name.replace(' ', '_'))
        r = self._rating()
        for _id in self._pl:
            self._season(self._pl[_id], season_name, r[_id][1])
            self._clear(self._pl[_id], False)
        print("Season added")

    @staticmethod
    def _clear(p, _all):
        for key in p:
            if not _all and key == "seasons":
                continue
            p[key] = type(p[key])()

    @staticmethod
    def _season(p, name, pos):
        p["seasons"][name] = {"pts": p["pts"], "count": p["count"], "wins": p["wins"], "pos": pos}

    def give_item(self, user_id, data=None):
        p = self.player(user_id)
        if data:
            for rare in self._items:
                if data[0] in self._items[rare]:
                    item = self._items[rare][data[0]]
                    if len(data) == 2:
                        value = data[1]
                    else:
                        value = item[2]
                    p["slots"][item[0]] = [data[0], rare, item[1], value]
                    return

    def set_rating(self, user_id, pts):
        if user_id not in self._pl:
            self._pl[user_id] = self._default([], [])
        self._pl[user_id]["pts"] = pts

    # ==== ========= ========= ========= ========= ========= ========= =========

    def player(self, user_id, slots=None, mods=None):
        if slots is None:
            slots = {}
        if mods is None:
            mods = []
        if user_id not in self._pl:
            print("create %s" % user_id)
            self._pl[user_id] = self._default(slots, mods)
        return self._pl[user_id]

    @staticmethod
    def _default(slots, mods):
        return {"slots": slots, "mods": mods, "seasons": {}, "wins": 0, "streak": 0, "count": 0, "pts": 0, "wrath": 0}

    def get_mod_keys(self):
        return self._mods.keys()

    def upgrade_item(self, current_item, new_item_rare):
        k = 1
        if current_item[3] < 0:
            k = -0.4
        current_item[3] += k*(self._upd[current_item[2]][current_item[1]]+self._upd[current_item[2]][new_item_rare])

    def _rating(self):
        _list = {}
        for _id in self._pl:
            if self._pl[_id]["count"] != 0:
                _list[_id] = self._pl[_id]["pts"]
        x = sorted(_list.items(), key=lambda kv: kv[1])
        x.reverse()
        _list = {}
        i = 1
        for obj in x:
            _list[obj[0]] = [obj[1], i]
            i += 1
        return _list

    # Рулетка случайных предметов
    # p - вероятность выпадения предмета (Сумма элеметов p_item не должна быть больше 100!)
    def _random_item(self, p_item, p=3):
        if random.random()*100 <= p:
            p_list = list(p_item)
            p_list.reverse()
            freq = [0] + p_list  # вычислим частоты  # вычислим частоты
            for rare in range(1, len(freq)):
                freq[rare] = freq[rare-1] + freq[rare]
            if freq[-1] > 100:  # Нужна ли нормализация?
                k = 100/freq[-1]
                for i in range(1, len(freq)):
                    freq[i] *= k
            elif freq[-1] != 100:
                freq += [100]
            freq.reverse()
            rnd = random.random()*100  # определим
            if rnd <= freq[0]:  # найдем интервал
                for rare in range(0, len(freq)-1):
                    if freq[rare] >= rnd > freq[rare+1]:
                        items = self._items[rare]
                        name = list(items.keys())[random.randint(0, len(items)-1)]
                        return items[name][0], [name, rare, items[name][1], items[name][2]]
        return None, None

    def _get_item(self, name):
        for rare in self._items:
            if name in self._items[rare]:
                return self._items[rare][name][0], [name, rare, self._items[rare][name][1], self._items[rare][name][2]]
        return None, None

    # ==== ========= ========= ========= ========= ========= ========= =========
    # Handler Block

    def _on_timer_duel(self, duel):
        if self._is_silence(duel["id"][0]):
            return
        if duel["accepted"]:
            msg = "[Дуэль готова] [id%d|%s] [id%d|%s]" % (duel["id"][0], duel["name"][0], duel["id"][1], duel["name"][1])
        else:
            msg = "[Дуэль отменена] %s %s" % (duel["name"][0], duel["name"][1])
        app().vk.send(self._task.duel_chat, msg)

    def _on_timer_item(self, item):
        self.upgrade_item(self.player(item["id"][0])["slots"][item["slot"]], item["item"][1])
        msg = "[Предмет %s автоулучшен]: %s" % (self._slots[item["slot"]], item["id"][1])
        try:
            app().vk.send(self._task.duel_chat, msg)
        except AttributeError:
            print(msg+" (для моментального автоулучшения установите wait_action = 0)")

    def _on_timer_save(self, obj, delay=900, save=True):
        with self._pl:  # !
            if save:
                self.save(self._path)
            self._task.append(delay, self._on_timer_save, obj)

    # ==== ========= ========= ========= ========= ========= ========= =========

    def h_duel(self, mp):
        if (mp.length == 1 and len(mp.fwd) == 0) or (mp.length > 1 and len(mp.fwd) > 0):
            return FN_CONTINUE
        user, unk = mp.find_nicknames(unk=True, is_all=False)
        if len(user) > 1:
            return mp.send("Сразу %d-х? Хах, а ты опасный человек! Но все-таки выбери кого-нибудь одного." % len(user))
        elif len(user) == 0:
            if len(unk) != 0 and mp.length == 2 and mp.words[1][0] == unk[0]:
                return mp.send(mp.ref() + ", ну ты что.. Присмотрись кого вызываешь на дуэль!")
            return FN_BREAK
        enemy_id = list(user.keys())[0]
        if enemy_id == mp.uid:
            return mp.send("Сам себя?! Оригинально...")
        if enemy_id <= 0:
            return FN_BREAK
        err_msg = "[id{0}|{1}], напишите ваш ник в vk.com/topic-177323563_40020608 и ожидайте обновления списков"
        if mp.nick is None:
            return mp.send(err_msg.format(mp.uid, mp.ref()))
        if user[enemy_id] is None:  # проверим возможно ли провести бой?
            return mp.send(err_msg.format(enemy_id, app().disk.user_profile(enemy_id).nick(None, True, "Оппонент")[0]))
        return self.fight_captcha_edition(mp, [enemy_id, user[enemy_id]])

    def h_ready(self, mp):
        if mp.length == 1:
            return self.fight_captcha_edition(mp, None)
        return FN_BREAK

    def h_item(self, mp):
        if mp.length == 1:
            with self._pl:  # !
                res = self._task.search(lambda key, obj: obj[1]["type"] == "item" and obj[1]["id"][0] == mp.uid, pop=True)
                if res is not None:
                    is_upg, res = mp.words[0][1][0] == 'у', res[0]
                    t = "» %s\n" % mp.ref(True)
                    mp.send(t + self.__on_item(self.player(mp.uid)["slots"], res["slot"], res["item"], is_upg, False))
        return FN_BREAK

    def h_change(self, mp):
        if mp.uid == app().disk.get("app", "admin_id", 481403141):
            res = mp.find_nicknames(False, is_all=False)
            if not res or len(res) != 1 or mp.length < 4:
                return FN_CONTINUE
            try:
                slot = int(mp.words[1][0])
                index = int(mp.words[2][0])
                value = mp.words[3][0].replace('_', ' ')
                if not (index == 0 or index == 4):
                    value = int(value)
                    if mp.words[2][2] == '-':
                        value *= -1
            except ValueError:
                return FN_CONTINUE
            with self._pl:  # !
                p = self.player(list(res.keys())[0])["slots"]
                if slot in p:
                    if index == 4:
                        if len(p[slot]) == 5:
                            if value in ['x', 'х']:
                                mp.send("Модификатор удалён: " + p[slot].pop(4))
                            else:
                                p[slot][index] = value
                                mp.send("Модификатор заменён: " + self._mods[value][0] + value)
                        else:
                            p[slot] += [value]
                            mp.send("Модификатор выдан: " + self._mods[value][0] + value)
                    else:
                        try:
                            p[slot][index] = value
                        except IndexError:
                            mp.send("Неверный индекс: " + str(index))
            return FN_BREAK
        return FN_CONTINUE

    def h_give(self, mp):
        is_admin = (mp.uid == app().disk.get("app", "admin_id", 481403141))
        if is_admin or mp.uid == 271993642:
            res = mp.find_nicknames(False, is_all=False)
            if not res:
                return FN_BREAK
            msg = ""
            with self._pl:  # !
                if is_admin and mp.length > 1:
                    if mp.length == 2 and mp.words[1][0].isnumeric():
                        wrath = int(mp.words[1][0])
                        if mp.words[0][2] == '-':
                            wrath *= -1
                        u = list(res.keys())[0]
                        p = self.player(u)
                        p["wrath"] += wrath
                        return mp.send("Получено очков ярости %s: %d ⇒ %d" % (res[u], p["wrath"]-wrath, p["wrath"]))
                    if mp.prefix[0] == '!':
                        try:
                            slot = int(mp.words[1][0])
                            name = mp.words[2][0].replace('_', ' ')
                            rare = int(mp.words[3][0])
                            param = int(mp.words[4][0])
                            value = int(mp.words[5][0])
                            if mp.words[4][2] == '-':
                                value *= -1
                            item = [name, rare, param, value]
                        except (IndexError, ValueError):
                            return FN_BREAK
                    else:
                        slot, item = self._get_item(mp.words[1][0].replace('_', ' '))
                    if slot is None or item is None:
                        return FN_BREAK
                    for user_id in res:
                        result = self._on_item(user_id, res[user_id], self.player(user_id)["slots"], slot, item)
                        if result:
                            msg += ("» %s\n" % res[user_id]) + result + "\n\n"
                else:
                    for user_id in res:
                        msg += ("» %s\n" % res[user_id]) + \
                               self.get_rnd_item(user_id, res[user_id], self.player(user_id)["slots"],
                                                 self._p_item[0], 100) + "\n\n"
            mp.send(msg)
        return FN_BREAK

    def h_stats(self, mp):
        user = mp.find_nicknames(count=1, is_all=False)
        _all = mp.words[0][2] == '+'
        if len(user) != 0:
            _id = list(user.keys())[0]
            user = user[_id]
        elif mp.length == 1:
            _id = mp.uid
            user = mp.ref(True)
        else:
            return FN_CONTINUE
        msg = "» %s\n" % user
        with self._pl:  # !
            s = self.player(_id)
            msg += "[Дуэли] 🏆%d 💢%d | Серия: 👑%d\nВ рейтинге: 🎖" % (s["pts"], s["wrath"], s["streak"])
            rating = self._rating()
            if _id in rating:
                msg += str(rating[_id][1])
            else:
                msg += str(len(rating) + 1)
            p = 0
            if s["count"] != 0:
                p = (s["wins"]/s["count"])*100
            msg += ". Игр: %d (%s)\n" % (s["count"], ("%.1f" % p)+'%')
            if _all:
                count = s["count"]
                msg_a = ""
                for ssn in s["seasons"]:
                    count += s["seasons"][ssn]["count"]
                    if s["seasons"][ssn]["count"] == 0:
                        continue
                    p = (s["seasons"][ssn]["wins"]/s["seasons"][ssn]["count"])*100
                    p = (("; побед %.1f" % p)+'%')*(int(p) != 0)
                    msg_a += "» %s: 🏆%d; игр: %d%s; 🎖%d\n" %\
                             (ssn, s["seasons"][ssn]["pts"], s["seasons"][ssn]["count"], p, s["seasons"][ssn]["pos"])
                msg += " (всего: %d)\n" % count
                if msg_a:
                    msg += msg_a + '\n'
            mods = _get_player_mods(s)
            if mods:
                msg_a, icons = self._print_mods(s["mods"], True)
                msg += "Модификаторы: " + ''.join(icons) + '\n'
                if _all:
                    msg += msg_a + self._print_mods(_invert_list(s["mods"], mods)) + '\n'
            p = list(self._std)
            if s["slots"]:
                if _all:
                    msg += "\nПредметы:\n"
                action, p[_CRT] = (2, -1), 100
                for slot in s["slots"]:
                    msg += self._print_item(action[_all], slot, s["slots"][slot]) + '\n'
                    if s["slots"][slot][3] > 0:
                        if s["slots"][slot][2] == 3:  # _CRT
                            p[s["slots"][slot][2]] -= p[s["slots"][slot][2]]*(s["slots"][slot][3]/100)
                        else:
                            p[s["slots"][slot][2]] += s["slots"][slot][3]
                p[_CRT] = 100-p[_CRT]
                # подкорректируем
                self._correct([p], one=True)
            msg += ("===== ===== ===== ===== ===== =====\n"
                    "❤ %.1f | 🛡 %.1f | 💣 %.1f |❗%.1f" % (p[_HP], p[_DEF], p[_DMG], p[_CRT])) + '%'
        return msg

    def h_rating(self, mp):
        if mp.length != 1:
            return FN_CONTINUE
        msg = ""
        with self._pl:  # !
            rating = self._rating()
            if not rating:
                return mp.send("Ещё ни один игрок не участвовал в новом сезоне!")
            if mp.uid not in rating:
                return mp.send("Вы еще не участвовали в новом сезоне!")
            cooldown = self._task.cooldown()
            _list = [[-1, -1]]*len(rating)
            i = 0
            for user_id in rating:
                _list[rating[user_id][1]-1] = [user_id, rating[user_id][0]]
                i += 1
            pos = rating[mp.uid][1]
            i, max_pos = 1, 10
            if max_pos < pos < max_pos+2:
                max_pos = pos+1
            for r in _list:
                msg += self._print_player(cooldown, i, r)
                i += 1
                if i > max_pos:
                    break
            if pos > max_pos:
                if pos-2 > max_pos:
                    msg += '...\n'
                for new_pos in range(pos-2, pos+1):
                    if new_pos < len(_list):
                        msg += self._print_player(cooldown, new_pos+1, _list[new_pos])
            msg_x = ""
            for new_pos in range(max_pos+1, len(_list)):
                if _list[new_pos][0] in cooldown:
                    msg_x += self._print_player(cooldown, -1, _list[new_pos], ", ")
            if msg_x != "":
                msg += "\nВ откате: " + msg_x[:len(msg_x) - 2]
        return mp.send(msg)

    def h_tracer(self, mp):
        if mp.uid in [app().disk.get("app", "admin_id", 481403141), 271993642]:
            mp.send(self.print_moves())
        return FN_BREAK

    def h_mods(self, mp):
        if mp.length != 1 or mp.uid != app().disk.get("app", "admin_id", 481403141) or mp.prefix[0] != '!':
            return FN_CONTINUE
        i, keys = 0, list(self._mods.keys())
        while i < len(keys)+50:
            mp.send(self._print_mods(keys[i:i+50], False, i+1))
            time.sleep(1)
            i += 50
        return FN_BREAK

    def h_set_mods(self, mp):
        if mp.length > 3:
            return FN_BREAK
        ids = []
        for w in mp.words:
            if not w[1].isnumeric() or 1 > int(w[1]) > 10:
                return FN_BREAK
            _id = int(w[1])
            if _id not in ids:
                ids += [_id]
        with self._pl:  # !
            res = self._task.search(lambda key, obj: obj[1]["type"] == "mods" and obj[1]["id"] == mp.uid, pop=True)
            if res is not None:
                x = 0
                for i in ids:
                    ids[x] = res[0]["mods"][i-1]
                    x += 1
                self.player(mp.uid)["mods"] = ids
                msg, icons = self._print_mods(ids, True)
                for i in range(0, len(icons)):
                    icons[i] += ids[i]
                mp.send("Установлены:\n" + '\n'.join(icons))
        return FN_BREAK

    def h_shop(self, mp):
        if mp.length != 1:
            return FN_BREAK
        msg = ""
        with self._pl:  # !
            p = self.player(mp.uid)
            if p["wrath"] < 3:
                mp.send("Недостаточно очков для открытия магазина!")
                return FN_BREAK
            a, k = sorted(_get_player_mods(p)), []
            for m in a:
                if m not in p["mods"]:
                    a.remove(m)
            if 10-len(p["mods"]) > 0:
                k = sorted(random.sample(_invert_list(a, self._mods.keys()), 10-len(a)))
            # Выведем иконки:
            desc = ""
            if a:
                msg_a, icons = self._print_mods(a, True, 1)
                r = ("-%s" % len(a))*(len(a) > 1)
                msg += ("[🎒 в рюкзаке 1%s] " % r) + ''.join(icons) + '\n'
                desc += msg_a
            if k:
                msg_a, icons = self._print_mods(k, True, len(a)+1)
                msg += ("[🛒 доступно %d-%d] " % (len(a)+1, 10)) + ''.join(icons)
                if mp.words[0][2] == '+':
                    msg += '\n\n' + desc + msg_a
            if msg:
                p["wrath"] -= 3
                self._task.append_mods(mp.uid, a+k, lambda obj: None)
                msg = self._act[3] + " " + mp.ref(True) + " (Выберите 3 модификатора):\n" + msg
            else:
                msg = "У вас нет доступных слотов под модификаторы!"
        return mp.send(msg)

    def h_check_captcha(self, mp):                  # проверка ответа на капчу
        if mp.length == 0 or mp.pid != self._task.duel_chat:
            return FN_CONTINUE
        for obj in self._last_duel:
            if mp.uid in obj["id"] and obj["ans"] is not None:
                if str(obj["ans"]) == mp.item["text"]:
                    obj["ans"] = None
                break
        return FN_BREAK

    # ==== ========= ========= ========= ========= ========= ========= =========
    # Captcha Block

    def fight_captcha_edition(self, mp, enemy):     # вызывается в h_..., но они не вызывают ни один метод класса
        with self._pl:  # !
            res = self._task.append_duel(mp, self._on_timer_duel, enemy)
            if res:
                msg, count = self._update_duel_info(res["id"])
                if msg is not None:
                    return mp.send(msg)
                ret = self.fight(res["id"], res["name"])
                if count >= 7:
                    ret[1] += random.randint(0, count//2)*0.015
                enemy = [res["id"][mp.uid == res["id"][0]], res["name"][mp.uid == res["id"][0]]]
                self._task.append_duel(mp, self._on_timer_duel, enemy, ret[1], True)
                mp.send(ret[0])

    def _is_silence(self, _id):
        for obj in self._last_duel:
            if _id in obj["id"]:
                return obj["hide"]
        return False

    def _update_duel_info(self, ids, c=4):
        for obj in self._last_duel:
            if ids[0] in obj["id"] and ids[1] in obj["id"]:
                if obj["ans"] is not None:
                    return "", obj["count"]
                obj["count"] += 1
                if obj["count"] % c == c-1:
                    obj["hide"] = True
                elif obj["count"] % c == 0:
                    obj["hide"] = False
                    obj["ans"], msg = _generate_captcha()
                    return msg, obj["count"]
                return None, obj["count"]
            elif ids[0] in obj["id"] or ids[1] in obj["id"]:
                self._last_duel.remove(obj)
                break
        self._last_duel += [{"id": ids, "count": 1, "hide": False, "ans": None}]
        return None, 1

    # ==== ========= ========= ========= ========= ========= ========= =========
    # Print Block

    def print_moves(self, length=0):
        if self._moves:
            names = self._moves.pop(-1)
            s, dmg, dmg_m, action, action_m = ["L", "W"], [0, 0], [0, 0], [0, 0], [0, 0]
            msg = "[Статистика последнего боя]: %s[%s] vs %s[%s]\nХод боя(%d): " % \
                  (names[0], s[0], names[1], s[1], len(self._moves))
            if self._moves and not self._moves[-1][1]:
                s.reverse()
            for move in self._moves:
                arr = ["", "", ""]
                if move[0] != "Удар":
                    if length:
                        arr[1] = "<%s>" % move[0][:length]
                    elif "Духовная Связь" in move[0]:
                        arr[1] = self._mods["Духовная Связь"][0]
                    elif "По Пальцам" in move[0]:
                        arr[1] = self._mods["По Пальцам"][0] + move[0][-1]
                    elif "Четырёхлистник" in move[0]:
                        arr[1] = self._mods["Четырёхлистник"][0] + move[0][-1]
                    else:
                        arr[1] = self._mods[move[0]][0]
                if move[2] is not None:
                    arr[0] = "%.1f" % move[2][0]
                if move[1] is None:
                    arr[2] = "[LR]"
                else:
                    arr[2] = "[%s]" % s[move[1]]
                    if move[2] is not None:
                        if move[0] == "Удар":
                            dmg[move[1]] += move[2][0]
                            action[move[1]] += 1
                        else:
                            dmg_m[move[1]] += move[2][0]
                            action_m[move[1]] += 1
                        arr[1] += '!'*move[2][1]
                msg += "".join(arr)+' '
            # Статистика
            for i in [0, 1]:
                try:
                    dmg[i] /= action[i]
                except ZeroDivisionError:
                    dmg[i] = 0
                try:
                    dmg_m[i] /= action_m[i]
                except ZeroDivisionError:
                    dmg_m[i] = 0
            msg += "\n\nСредний урон: {2:.1f}+{3:.1f}[{0}] | {4:.1f}+{5:.1f}[{1}]\n" \
                   "Кол-во действий: {6}+{7}[{0}] | {8}+{9}[{1}]".\
                format(s[0], s[1], dmg[0], dmg_m[0], dmg[1], dmg_m[1], action[0], action_m[0], action[1], action_m[1])
            return msg
        return ""

    def _print_item(self, action, slot, item, new_item=None):
        m, c = '', ('%'*(item[2] == _CRT))+"👥"*(item[3] < 0)
        if len(item) == 5:
            if item[4] in self._mods:
                m = " %s " % self._mods[item[4]][0]
            else:
                m = " &#0;"
        name = "%s%s [%s]" % (item[0], m,  self._rare[item[1]])
        if action == 2:         # Получен новый предмет, Сокращенная версия статистики
            return self._slots[slot] + ' ' + name + " (%s%.1f%s)" % (self._params[item[2]], item[3], c)
        elif action < 0:        # Полная версия статистики
            try:
                v = self._items[item[1]][item[0]][2]
            except KeyError:
                v = item[3]
            s = (('+' * (item[3] > 0)) + ("%.1f" % (item[3]-v)))*(item[3]-v != 0)
            return self._slots[slot] + ' ' + name + " (%s%d%s%s)" % (self._params[item[2]], v, s, c)
        else:
            if action == 0:  # Замена, Заменено
                s = ('%'*(new_item == _CRT))+"👥"*(new_item[3] < 0)
            else:
                s = c
            old_value = "%s%.1f%s" % (self._params[item[2]], item[3], c)
            new_value = "%.1f%s" % (new_item[3], s)
            new_rare = (" [%s]" % self._rare[new_item[1]])*(action == 0)
            if item[2] != new_item[2]:
                new_value = self._params[new_item[2]] + new_value
            if action == 0:
                return "%s%s %s ⇒ %s (%s)" % (self._slots[slot], new_rare, new_value, name, old_value)
            return self._slots[slot] + ' ' + name + new_rare + " (" + old_value + '⇒' + new_value + ')'

    def _print_mods(self, names, ret_icons=False, num=None):
        icon, msg = [], ""
        for name in names:
            if name not in self._mods:
                continue
            icon += [self._mods[name][0]]
            if num is not None:
                msg += "%s. " % num
                num += 1
            msg += self._mods[name][0] + name + "\n➜ "
            if type(self._mods[name][2]) is tuple:
                if len(self._mods[name][2]) == 2:
                    msg += self._mods[name][1] % (self._mods[name][2][0], self._mods[name][2][1])
                else:
                    msg += self._mods[name][1] % (self._mods[name][2][0], self._mods[name][2][1], self._mods[name][2][2])
            elif self._mods[name][2] is None:
                msg += self._mods[name][1]
            else:
                msg += self._mods[name][1] % self._mods[name][2]
            msg += '\n'
        if ret_icons:
            return msg, icon
        return msg

    def _print_player(self, cooldown, i, r, sep='\n'):
        msg = ""
        if i > 0:
            if i < 10:
                msg += '0'
            msg += str(i) + ". "
        msg += app().disk.user_profile(r[0]).nick(None, True, "?")[0]
        if i > 0:
            msg += " (" + str(r[1]) + " pts)"
        return msg + _print_cooldown(cooldown, r[0]) + ' 🦌'*(self.player(r[0])["streak"] >= 3) + sep

    def preview(self, mp, rnd_item=3.5, rnd_mod=0.2):       # Используется из вне
        msg_chat, msg_duel = "", ""
        with self._pl:
            p, nick, a = self.player(mp.uid), mp.ref(True), 'а'*(not mp.is_man)
            # Попытаемся выдать случайный предмет
            slot, item = self._random_item(self._p_item[1], rnd_item)
            res = self._on_item(mp.uid, nick, p["slots"], slot, item)
            if res:
                temp = "→ %s\n%s"
                msg_duel += temp % (nick, res)
                msg_chat += (temp % (nick + "\nПолучено:", self._print_item(2, slot, item))) + '\n'
            # Попытаемся выдать модификатор на предмет
            if p["slots"] and random.random()*100 <= rnd_mod:
                _mods = _invert_list(_get_player_mods(p), self._mods.keys())
                slots = []
                for slot in p["slots"]:
                    if len(p["slots"][slot]) != 5:
                        slots += [slot]
                if slots:
                    name = random.sample(_mods, 1)[0]
                    icon = self._mods[name][0]
                    slot = random.sample(slots, 1)[0]
                    p["slots"][slot] += [name]
                    temp = "→ %s получил%s модификатор %s" % (nick, a, icon)
                    msg_chat += temp
                    msg_duel += temp + name + '\nУстановлено на ' + self._print_item(2, slot, p["slots"][slot])
        if mp.pid != self._task.duel_chat and msg_chat != "":
            msg_chat += "\nЗа подробностями в беседу «Дуэль»"
            mp.send(msg_chat)
        mp.send(msg_duel, peer_id=self._task.duel_chat)

    # ==== ========= ========= ========= ========= ========= ========= =========
    # Fight Block

    def _is_death(self, m, k, a, pl, last):
        if _is_mod(m[a], "Двойник"):
            self._moves += [("Двойник", a, None)]
            pl[a][_HP] = last
            return False
        if _is_mod_rnd(m[a], "Феникс", self._mods["Феникс"][2][0]*k[2][a]):
            pl[a][_HP] = self._mods["Феникс"][2][1]
            self._moves += [("Феникс", a, None)]
            return False
        return True

    def _upd_mods(self, pl, m, k, exchange, names):
        for i in [0, 1]:
            enemy = not i
            for name in names:
                if name in m[i] and m[i][name]:
                    _dec(m[i][name])
                    if exchange:
                        value = pl[enemy][self._mods[name][3]]*(k[2][i]*(self._mods[name][2]/100))
                        pl[enemy][self._mods[name][3]] -= value
                        pl[i][self._mods[name][3]] += value
                    else:
                        pl[enemy][self._mods[name][3]] *= 1-(k[2][i]*(self._mods[name][2]/100))

    def _stage0(self, m, pl, s, ids, nicknames):
        # ===== ===== ===== Подготовительный этап ===== ===== =====
        flag = bool(random.randint(0, 1))
        for i in [flag, not flag]:
            if m[not i] and _is_mod(m[i], "Жадность"):
                key = random.sample(m[not i].keys(), 1)[0]
                if key in m[i]:
                    if m[not i][key][0] > 0:
                        m[i][key][0] += 1
                    m[not i].pop(key)
                else:
                    m[i][key] = m[not i].pop(key)
                    s[i]["mods"] += [key]
                s[not i]["mods"].remove(key)
            if m[not i] and _is_mod(m[i], "Запрет"):
                m[not i].pop(random.sample(m[not i].keys(), 1)[0])
        k = [_is_mod(m[0], "Благословение"), _is_mod(m[1], "Благословение"), [1, 1]]
        for i in [0, 1]:
            if k[i]:
                k[2][i] = self._mods["Благословение"][2]
                for name in m[i]:
                    if name in ["Амулет Ведьмака", "Рок Судьбы", "Инициатор", "Дары Смерти", "Чёрная Метка", "Двойник",
                                "Закаленная Сталь", "Фатальная Ошибка", "Духовная Связь", "Подарок", "Ручная Сова",
                                "Маховик Времени", "Скрещенные Пальцы", "Альфа-Самец", "Запрет", "Жадность"]:
                        m[i][name][0] += 1
        v = [_is_mod(m[0], "Амулет Ведьмака"), _is_mod(m[1], "Амулет Ведьмака")]
        if v == [True, True]:
            m[0] = m[1] = {}
            if random.randint(0, 1) == 1:
                _reverse(pl, m, s, ids, nicknames, k)
            return k
        elif v[0] or v[1]:
            m[not v[1]] = {}
        if is_exchange(m, "Рок Судьбы"):
            m[0], m[1] = m[1], m[0]
            s[0]["mods"], s[1]["mods"] = s[1]["mods"], s[0]["mods"]
            flag = "Рок Судьбы" in m[0]
            print(m[flag], m[not flag])
            m[flag]["Рок Судьбы"] = m[not flag].pop("Рок Судьбы")
            s[flag]["mods"] += ["Рок Судьбы"]
            s[not flag]["mods"].remove("Рок Судьбы")
        if "Инициатор" in m[1] and "Инициатор" in m[0]:
            _dec(m[flag]["Инициатор"])
        elif _is_mod(m[0], "Инициатор"):
            flag = False
        elif _is_mod(m[1], "Инициатор"):
            flag = True
        if flag:
            _reverse(pl, m, s, ids, nicknames, k)
        for i in [0, 1]:
            if s[i]["streak"] < 3 and _is_mod(m[i], "Альфа-Самец"):
                s[i]["streak"] = 3
            if s[i]["pts"] >= 5 and _is_mod(m[i], "Очки"):
                s[i]["pts"] -= self._mods["Очки"][2][0]
                s[i]["wrath"] += self._mods["Очки"][2][1]*k[2][i]
        for i in [0, 1]:    # _is_mod не менять на _is_mod_rnd
            if _is_mod(m[i], "Дары Смерти") and random.random()*100 <= self._mods["Дары Смерти"][2]:
                if self._is_death(m, k, not i, pl, pl[not i][_HP]):
                    self._moves += [("Дары Смерти", bool(i), None)]
                    return k
        # ===== ===== ===== Постоянные модификаторы направленные на себя ===== ===== =====
        for i in [0, 1]:
            if _is_mod(m[i], "Геракл"):
                pl[i][_DMG] += self._mods["Геракл"][2][1]
            if _is_mod(m[i], "Пацифист"):
                pl[i][_HP] *= self._mods["Пацифист"][2][0]
            if _is_mod(m[i], "Уязвимые Места"):
                pl[i][_CRT_DMG] += self._mods["Уязвимые Места"][2]*k[2][i]
            if "Везунчик" in m[i]:
                pl[i][_CRT_DMG] += self._mods["Везунчик"][2]*k[2][i]
            if "Точность" in m[i]:      # позже установим флаг, что использовано
                pl[i][_DMG] *= 1+((self._mods["Точность"][2]/100)*k[2][i])
            if _is_mod(m[i], "Защитная Экипировка"):
                pl[i][_DEF] += self._mods["Защитная Экипировка"][2][0]+8*k[i]
            for name in ["Крепкий Хребет", "Концентрация", "Адреналин", "Молитва"]:
                if _is_mod(m[i], name):
                    pl[i][self._mods[name][3]] += self._mods[name][2]*k[2][i]
        stats = [list(pl[0]), list(pl[1])]
        # ===== ===== ===== Постоянные дебафы (свои) ===== ===== =====
        for i in [0, 1]:
            if _is_mod(m[i], "Щит Хавела"):
                pl[i][_DEF] *= 1+(k[2][i]*(self._mods["Щит Хавела"][2][0]/100))
                pl[i][_DMG] *= 1-(k[2][i]*(self._mods["Щит Хавела"][2][1]/100))
            if _is_mod(m[i], "Карма"):
                pl[i][_DEF] *= 1-(k[2][i]*(self._mods["Карма"][2][0]/100))
                pl[i][_CRT_DMG] += k[2][i]*self._mods["Карма"][2][1]
            if _is_mod(m[i], "Безумец"):
                pl[i][_DEF] = 0
        # ===== ===== ===== Постоянные дебафы (общие) ===== ===== =====
        self._upd_mods(pl, m, k, True, ["Поглощение Жизни", "Воровство"])
        # ===== ===== ===== Постоянные дебафы (чужие) ===== ===== =====
        self._upd_mods(pl, m, k, False, ["Сердцебиение", "Прорубающее Лезвие", "Дыхание Мертвеца", "Критический Уровень"])
        # ===== ===== ===== Спеллы (перед боем) ===== ===== =====
        for i in [0, 1]:
            if _is_mod(m[i], "Армагеддон"):
                for j in [0, 1]:
                    k_dmg = pl[j][_HP]/self._max[_HP]
                    last = pl[j][_HP]
                    pl[j][_HP] *= 1-(k_dmg*(self._mods["Армагеддон"][2]/100)*k[2][i])
                    self._moves += [("Армагеддон", bool(j), (last-pl[j][_HP], False))]
        # ===== ===== ===== Крупные дебаффы ===== ===== =====
        for i in [0, 1]:
            if _is_mod(m[i], "Закаленная Сталь"):
                pl[not i][_CRT] = 0
        if is_exchange(m, "Фатальная Ошибка"):
            pl[0][0], pl[1][0] = pl[1][0], pl[0][0]
        # ===== ===== ===== Защитные средства ===== ===== =====
        for i in [0, 1]:
            if _is_mod(m[i], "Скрещенные Пальцы"):
                pl[i] = stats[i]
        return k

    def _scatter(self, m, k):
        scatter = (0.9, 1.1)
        if _is_mod(m, "Опьянение"):
            scatter = self._mods["Опьянение"][2]
            if k:
                scatter = (scatter[0], scatter[1]+(scatter[1]-1)*(k-1))
        elif _is_mod(m, "Точность"):
            scatter = (1, 1)
        return scatter

    def _correct(self, pl, limited=True, one=False):
        for p in pl:
            for i in range(0, len(self._params)-1):
                if p[i] <= 0:
                    if i == _HP:
                        p[i] = 1
                    else:
                        p[i] = 0
                if limited and p[i] > self._max[i]:
                    p[i] = self._max[i]
            if one:
                break
            limited = True

    def _heal(self, pl, m, a, k, dmg):
        heal = 0
        if "Вампиризм" in m[a]:
            _dec(m[a]["Вампиризм"])
            heal += dmg*(self._mods["Вампиризм"][2]/100)*k[2][a]
            self._moves += [("Вампиризм", a, (heal, False))]
        if "Молодильные Яблоки" in m[a]:
            _dec(m[a]["Молодильные Яблоки"])
            heal += pl[a][_HP]*(self._mods["Молодильные Яблоки"][2]/100)*k[2][a]
            self._moves += [("Молодильные Яблоки", a, (heal, False))]
        pl[a][_HP] += heal

    def _on_hit(self, pl, m, a, dmg, is_crit, k, name="Удар"):
        last = pl[not a][_HP]
        if "Духовная Связь" in m[not a]:
            _dec(m[not a]["Духовная Связь"])
            dmg = dmg/2
            pl[0][_HP] -= dmg
            pl[1][_HP] -= dmg
            self._moves += [("Духовная Связь (%s)" % name, None, (dmg, is_crit))]
            self._heal(pl, m, not a, k, dmg)
        else:
            pl[not a][_HP] -= dmg
            self._moves += [(name, a, (dmg, is_crit))]
        self._heal(pl, m, a, k, dmg)
        if pl[not a][_HP] < 0:
            self._is_death(m, k, not a, pl, last)

    def _dmg(self, pl, s, m, k, _max, a, scatter):
        if "Пацифист" in m[a] and not _on_skip_move(m, a):
            m[a]["Пацифист"][2] += 1
            if ((k[a] and (m[a]["Пацифист"][2] % 2 != 1)) or
               (not k[a] and m[a]["Пацифист"][2] % self._mods["Пацифист"][2][1] != 1)):
                return 0, False
        if "Забвение" in m[not a] and m[not a]["Забвение"][2] == 0 and \
           m[not a]["Забвение"][1] < self._mods["Забвение"][2][0] and not _on_skip_move(m, not a):
            if random.random()*100 > self._mods["Забвение"][2][1]/k[2][not a]:
                _dec(m[not a]["Забвение"])
                self._moves += [("Забвение", a, None)]
                return 0, False
            else:
                m[not a]["Забвение"][2] = 1
        if "Коррозия Брони" in m[a] and m[a]["Коррозия Брони"][1] < self._mods["Коррозия Брони"][2]+k[2][a]:
            _dec(m[a]["Коррозия Брони"])
            pl[not a][_DEF] = 0
            self._moves += [("Коррозия Брони", not a, None)]
        if "Неожиданные Атаки" in m[a] and m[a]["Неожиданные Атаки"][1] < self._mods["Неожиданные Атаки"][2]*k[2][a]:
            _dec(m[a]["Неожиданные Атаки"])
            pl[a][_CRT] = 100
            self._moves += [("Неожиданные Атаки", a, None)]
        elif "Иглы" in m[a]:
            m[a]["Иглы"][2] += 1
            if m[a]["Иглы"][2] % (self._mods["Иглы"][2]-(2*k[a])) == 0:
                _dec(m[a]["Иглы"])
                pl[a][_CRT] = 100
                self._moves += [("Иглы", a, None)]
        dmg, is_crit = _dmg(pl, a, scatter[a])
        pl[not a][_DEF] = _max[not a][_DEF]
        pl[a][_CRT] = _max[a][_CRT]
        if "Четырёхлистник" in m[a] and m[a]["Четырёхлистник"][2] < self._mods["Четырёхлистник"][2][0]*k[2][a] and \
           random.random()*100 < self._mods["Четырёхлистник"][2][1]:
            _dec(m[a]["Четырёхлистник"])
            key = random.sample(_invert_list(_get_player_mods(s[a]), self._mods.keys()), 1)[0]
            if key:
                m[a]["Четырёхлистник"][2] += 1
                s[a]["mods"] += [key]
                m[a][key] = [1, 0, 0]
                self._moves += [("Четырёхлистник" + self._mods[key][0], a, None)]
        if "По Пальцам" in m[a]:
            _dec(m[a]["По Пальцам"])
            if m[a]["По Пальцам"][2] != 0:
                pl[not a][m[a]["По Пальцам"][2]-1] += m[a]["По Пальцам"][3]
            m[a]["По Пальцам"] = [0, 1, random.randint(0, _CRT)+1, 0]
            v = pl[not a][m[a]["По Пальцам"][2]-1]*(self._mods["По Пальцам"][2]/100)*k[2][a]
            m[a]["По Пальцам"][3] = v
            pl[not a][m[a]["По Пальцам"][2]-1] -= v
            self._moves += [("По Пальцам"+self._params[m[a]["По Пальцам"][2]-1], not a, None)]
        if "Чёрная Метка" in m[not a] and "Чёрная Метка" not in m[a]:
            m[not a]["Чёрная Метка"] = [0, 1]
            p = list(self._mods["Чёрная Метка"][2])
            _max[not a][_HP] = p[0]
            for j in range(0, len(p)):
                p[j] *= k[2][not a]
            p.insert(_DMG, pl[not a][_DMG])
            pl[not a] = p + [pl[not a][_CRT_DMG]]
        if "Элексир" in m[a]:
            m[a]["Элексир"] = [0, 1]
            dmg += ((1-(pl[a][_HP]/_max[a][_HP]))*100)*self._mods["Элексир"][2]*k[2][a]
        if "Агония" in m[a] and pl[a][_HP]/_max[a][_HP] < self._mods["Агония"][2][1]/100:
            m[a]["Агония"] = [0, 1]
            dmg *= self._mods["Агония"][2][0]*k[2][a]
        if ("Призрак" in m[a] and m[a]["Призрак"][0] != 0) or ("Призрак" in m[not a] and m[not a]["Призрак"][0] != 0):
            hit = random.randint(0, 1)
            if random.random()*100 < self._mods["Призрак"][2][0]:
                self._moves += [("Призрак", hit, (1, False))]
                _dec(m["Призрак" in m[1]]["Призрак"])
                v = _max[hit][_DMG]*(1+((self._mods["Призрак"][2][2]*k[2][hit])/100))
                pl[hit][_DMG] += v-_max[hit][_DMG]
                _max[hit][_DMG] = v
                if "Призрак" not in m[hit]:
                    m[hit]["Призрак"] = m[not hit].pop("Призрак")
                    m[hit]["Призрак"] = [0, 1]
                    s[hit]["mods"] += ["Призрак"]
                    s[not hit]["mods"].remove("Призрак")
            else:
                self._moves += [("Призрак", hit, None)]
            if hit == a:
                if "Забвение" in m[not a] and m[not a]["Забвение"][2] == 0 and \
                   m[not a]["Забвение"][1] < self._mods["Забвение"][2][0] and not _on_skip_move(m, not a):
                    self._moves += [("Забвение", not a, None)]
                    return 0, False
                dmg, is_crit = _dmg(pl, not hit, scatter[not hit])
                dmg *= 1 + (self._mods["Призрак"][2][1]/100)
                a = not a
            self._on_damage(m, pl, _max, dmg, is_crit, a, k)
            return 0, False
        if "Нокаут" in m[a] and not _on_skip_move(m, not a):
            if m[a]["Нокаут"][2] == 0:
                _dec(m[a]["Нокаут"])
            if m[a]["Нокаут"][2] >= 0:
                m[a]["Нокаут"][2] += 1
            if 0 < m[a]["Нокаут"][2] < self._mods["Нокаут"][2][0]-2*(k[a]):
                return 0, False
            if m[a]["Нокаут"][2] > 0:
                m[a]["Нокаут"][2] = -1
                dmg = self._mods["Нокаут"][2][1]
                if is_crit:
                    dmg *= pl[0][_CRT_DMG]
        return dmg, is_crit

    def _on_escape_damage(self, pl, m, a, k):
        if "Инстинкт Зверя" in m[not a] and m[not a]["Инстинкт Зверя"][1] < self._mods["Инстинкт Зверя"][2]*k[2][not a]:
            _dec(m[not a]["Инстинкт Зверя"])
            self._moves += [("Инстинкт Зверя", not a, None)]
            return True
        if "Оглушающий Удар" in m[not a] and (m[not a]["Оглушающий Удар"][2] > 0 or
                                              random.random()*100 < self._mods["Оглушающий Удар"][2][0]):
            if m[not a]["Оглушающий Удар"][2] == 0:
                _dec(m[not a]["Оглушающий Удар"])
                m[not a]["Оглушающий Удар"][2] = self._mods["Оглушающий Удар"][2][1]*k[2][not a]
            m[not a]["Оглушающий Удар"][2] -= 1
            self._moves += [("Оглушающий Удар", a, None)]
            return True
        if _is_mod_rnd(m[not a], "Ловкость", self._mods["Ловкость"][2][0]*k[2][not a]):
            pl[not a][_CRT] += self._mods["Ловкость"][2][1]
            self._moves += [("Ловкость", not a, None)]
            return True
        return False

    def _on_damage(self, m, pl, _max, dmg, is_crit, a, k):
        if self._on_escape_damage(pl, m, a, k):
            return
        # ===== ===== ===== ===== ===== ===== ===== =====
        hp_increase = _is_mod(m[not a], "Сытный Обед")
        if hp_increase:
            pl[not a][_HP] += self._mods["Сытный Обед"][2]*k[2][not a]
            self._moves += [("Сытный Обед", not a, None)]
        if "Болевой Порог" in m[not a] and dmg >= self._mods["Болевой Порог"][2]:
            _dec(m[not a]["Болевой Порог"])
            self._moves += [("Болевой Порог", not a, None)]
            dmg = self._mods["Болевой Порог"][2]/k[2][not a]
        if "Панцирь" in m[not a] and random.random()*100 < self._mods["Панцирь"][2][0]*k[2][not a]:
            _dec(m[not a]["Панцирь"])
            self._moves += [("Панцирь", not a, None)]
            dmg *= self._mods["Панцирь"][2][1]/100
        # ===== ===== ===== ===== ===== ===== ===== =====
        self._on_hit(pl, m, a, dmg, is_crit, k)
        # ===== ===== ===== ===== ===== ===== ===== =====
        if "Губка" in m[not a]:
            if m[not a]["Губка"][2] == 0:
                m[not a]["Губка"] += [0]
            m[not a]["Губка"][2] += 1
            m[not a]["Губка"][3] += dmg*((self._mods["Губка"][2][0]*k[2][not a])/100)
            if m[not a]["Губка"][2] % self._mods["Губка"][2][1] == 0:
                _dec(m[not a]["Губка"])
                self._moves += [("Губка", not a, (m[not a]["Губка"][3], False))]
                pl[a][_HP] -= m[not a]["Губка"][3]
                m[not a]["Губка"][3] = 0
        if "Защитная Экипировка" in m[not a] and is_crit and \
           pl[not a][_DEF] - self._mods["Защитная Экипировка"][2][1] >= 0:
            m[not a]["Защитная Экипировка"][1] += 1
            pl[not a][_DEF] -= self._mods["Защитная Экипировка"][2][1]
            _max[not a][_DEF] -= self._mods["Защитная Экипировка"][2][1]
        if "Торнадо" in m[a]:
            _dec(m[a]["Торнадо"])
            hit_to = bool(random.randint(0, 1))
            damage = self._mods["Торнадо"][2]*k[2][a]
            pl[hit_to][_HP] -= damage
            self._moves += [("Торнадо", not hit_to, (damage, False))]
        if "Воспламенение" in m[a]:
            if m[a]["Воспламенение"][2] > 0:
                m[a]["Воспламенение"][2] -= 1
                damage = self._mods["Воспламенение"][2][2]*k[2][a]
                pl[not a][_HP] -= damage
                self._moves += [("Воспламенение", a, (damage, False))]
            elif random.random()*100 < self._mods["Воспламенение"][2][0]:
                _dec(m[a]["Воспламенение"])
                m[a]["Воспламенение"][2] = self._mods["Воспламенение"][2][1]
        if _is_mod_rnd(m[a], "Мьельнир", self._mods["Мьельнир"][2][0]):
            damage = dmg*(k[2][a]*(self._mods["Мьельнир"][2][1]/100))
            pl[not a][_HP] -= damage
            self._moves += [("Мьельнир", a, (damage, False))]
        if "Яд" in m[a]:
            _dec(m[a]["Яд"])
            count = m[a]["Яд"][1]
            if count > self._mods["Яд"][2][1]:
                count = self._mods["Яд"][2][1]
            damage = count*self._mods["Яд"][2][0]*k[2][a]
            pl[not a][_HP] -= damage
            self._moves += [("Яд", a, (damage, False))]
        if "Эфес" in m[a]:
            m[a]["Эфес"][2] += 1
            if m[a]["Эфес"][2] % self._mods["Эфес"][2] == 0 and not self._on_escape_damage(pl, m, a, k):
                _dec(m[a]["Эфес"])
                damage = dmg*k[2][not a]
                pl[not a][_HP] -= damage
                self._moves += [("Эфес", a, (damage, is_crit))]
        if _is_mod_rnd(m[a], "Бодрость", self._mods["Бодрость"][2][0]):
            damage = (dmg*k[2][not a]*self._mods["Бодрость"][2][1])-dmg
            pl[not a][_HP] -= damage
            self._moves += [("Бодрость", a, (damage, is_crit))]
        # ===== ===== ===== ===== ===== ===== ===== =====
        if pl[not a][0] > 0 and hp_increase and pl[not a][_HP] > self._mods["Сытный Обед"][2]*k[2][not a]:
            pl[not a][_HP] -= self._mods["Сытный Обед"][2]*k[2][not a]

    def _init_mods(self, p):
        _list = {}
        for m in _get_player_mods(p):
            if m in self._mods:
                if m in ["Оглушающий Удар", "Эфес", "Пацифист", "Нокаут", "Воспламенение", "По Пальцам",
                         "Четырёхлистник", "Забвение", "Иглы", "Губка"]:
                    _list[m] = [1, 0, 0]
                else:
                    _list[m] = [1, 0]
            else:
                print("Неизвестный модификатор: " + m)
        return _list

    def fight(self, ids, names, limited=True, simulator=False):
        s = [self.player(ids[0]), self.player(ids[1])]
        _max = [list(self._std), list(self._std)]
        m = [self._init_mods(s[0]), self._init_mods(s[1])]

        calc_stats(s[0]["slots"], _max[0], _max[1])
        calc_stats(s[1]["slots"], _max[1], _max[0])
        self._correct(_max, limited)
        self._moves.clear()
        k, pl = self._stage0(m, _max, s, ids, names), [list(_max[0]), list(_max[1])]
        if self._moves and self._moves[-1][0] == "Дары Смерти":
            return self._on_end_battle(not self._moves[-1][1], pl, m, s, ids, names, k, _max, simulator)

        scatter = [self._scatter(m[0], k[2][0]), self._scatter(m[1], k[2][1])]
        attacker = True
        while pl[0][0] > 0 and pl[1][0] > 0:
            attacker = not attacker
            dmg, is_crit = self._dmg(pl, s, m, k, _max, attacker, scatter)
            if dmg == 0:
                continue
            self._on_damage(m, pl, _max, dmg, is_crit, attacker, k)
            # ===== ===== ===== ===== ===== ===== ===== =====
            if pl[not attacker][0] > 0:
                if _is_mod_rnd(m[not attacker], "Контрудар", self._mods["Контрудар"][2]*k[2][not attacker]):
                    damage, is_crit = self._dmg(pl, s, m, k, _max, not attacker, scatter)
                    if not self._on_escape_damage(pl, m, not attacker, k):
                        self._on_hit(pl, m, not attacker, damage, is_crit, k, "Контрудар")
                # В конце всех в данном блоке
                if "Увядание" in m[attacker]:
                    _dec(m[attacker]["Увядание"])
                    if len(m[attacker]["Увядание"]) == 2:
                        m[attacker]["Увядание"] += [_max[not attacker][_HP]*(self._mods["Увядание"][2]/100)*k[2][attacker]]
                    pl[not attacker][_HP] -= m[attacker]["Увядание"][2]
                    self._moves += [("Увядание", not attacker, (m[attacker]["Увядание"][2], False))]
        if pl[0][_HP] < 0 and pl[1][_HP] < 0:
            if self._moves and self._moves[-1][0] == "Торнадо":
                i = not self._moves[-1][1]
                pl[i][_HP] += self._moves[-1][2][0]
                _dec(m[i]["Торнадо"])
                self._moves.pop(-1)
            else:
                pl[0][_HP] = 0.1
                print("duel hp0: ", self._moves[-1])
        for p in pl:
            if p[_HP] < 0:
                p[_HP] = 0
        return self._on_end_battle(pl[1][_HP] == 0, pl, m, s, ids, names, k, _max, simulator)

    def _on_end_battle(self, loser_p2, pl, m, s, ids, names, k, _max, simulator):
        if loser_p2:
            _reverse(pl, m, s, ids, names, k)
            _max.reverse()
        return self._print(pl, s, self._used(s, m, k, names, simulator), ids, names, _max, simulator)

    def _used(self, s, m, k, names, simulator):     # m[0] - проигравший, m[1] - победитель
        msg, cooldown, wrath, pts = ["", ""], 1, 0, 0
        # Модификаторы, не влияющие на ход боя
        for i in [0, 1]:
            if s[i]["slots"] and _is_mod(m[i], "Подарок"):
                slot = random.sample(s[i]["slots"].keys(), 1)[0]
                last = list(s[i]["slots"][slot])
                self.upgrade_item(s[i]["slots"][slot], _C)
                msg[i] += "%s %s\n" % (self._act[1], self._print_item(1, slot, last, s[i]["slots"][slot]))
        p_items = [[list(self._p_item[0]), 100], [[0, 0, 0, 0], 0]]
        if _is_mod(m[0], "Антиквар"):
            p_items[0][0][_R-1] += self._mods["Антиквар"][2]*k[2][0]
        if "Безумец" in m[1]:
            p_items[1][0][_E-1] = 100
            p_items[1][1] = self._mods["Безумец"][2]*k[2][1]
        if "Геракл" in m[0]:
            p_items[0][0][_L-1] *= self._mods["Геракл"][2][0]*k[2][0]
        if _is_mod(m[0], "Акция"):
            wrath = self._mods["Акция"][2]*k[2][0]
        if _is_mod(m[1], "Заказ"):
            pts = self._mods["Заказ"][2]*k[2][1]
        for i in [0, 1]:    # должно быть в порядке % убывания отката
            if "Ручная Сова" in m[i]:
                h = datetime.datetime.now().hour
                if self._mods["Ручная Сова"][2][0] <= (h+3) % 24 <= self._mods["Ручная Сова"][2][1]:
                    _dec(m[i]["Ручная Сова"])
                    cooldown -= cooldown*(self._mods["Ручная Сова"][2][2]/100)
            if _is_mod(m[i], "Маховик Времени"):
                cooldown -= cooldown*((self._mods["Маховик Времени"][2])/100)
        # Теперь определим кто какие модификации использовал
        used = ["", ""]
        for i in [0, 1]:
            for mod in m[i]:
                if m[i][mod][1] > 0:
                    if not simulator and mod in s[i]["mods"] and m[i][mod][0] == 0:
                        s[i]["mods"].remove(mod)
                    used[i] += "%s x%d, " % (self._mods[mod][0], m[i][mod][1])
            if used[i] != "":
                used[i] = "|| " + used[i][:-2]
        # Должно быть в конце. Больше изменений self._moves не происходит!
        self._moves += [names]
        return {"used": used, "p": p_items, "cd": cooldown, "wrath": wrath, "msg": msg, "pts": pts}

    def _print(self, pl, s, data, ids, names, _max, simulator):
        boss = [s[0]["streak"] >= 3, s[1]["streak"] >= 3]
        wrath, pts, streak = 1, [-1*(s[0]["pts"] > 0), 1], [0, 1]
        # print("===== ===== ===== ===== ===== ===== ====== ===== ===== ======\n%s\n\n%s\n" % (pl, self.print_moves(6)))
        if not simulator:
            if s[0]["pts"] == 0:
                pts[0] = 0
            if boss[0] and boss[1]:                             # Два босса сражались
                wrath = 0
                data["p"][0][0] = [0, 0, 0, 0]                  # Боссы не могут получить редкие предметы
            elif boss[0] and not boss[1]:                       # Босс проиграл обычному игроку
                wrath = 3
                p_item = list(self._p_item[0])                  # Увеличим победителю шанс выпадения редкого предмета
                p_item[_R-1] *= 2.5
                data["p"][1][1] = 100
                for rare in range(0, len(p_item)):
                    data["p"][1][0][rare] += p_item[rare]
            elif not boss[0] and boss[1]:                       # Обычный игрок проиграл боссу
                pts[1] = 2
            if boss[0] != boss[1]:                              # Играл обычный игрок с боссом
                data["cd"] *= 0.75                              # Уменьшим откат
                for rare in range(0, len(self._p_item[0])):     # Распространяется и на босса, если проиграет
                    data["p"][0][0][rare] *= 0.8                # Шанс выпад.редк.предметов умен.проигравшему
        # Выведем информацию о бое
        wrath += data["wrath"]
        pts[1] += data["pts"]
        str_streak = (" 👑%d" % s[1]["streak"])*(s[1]["streak"] > 1)
        str_pts = ("%d" % pts[0])*(pts[0])
        msg  = "❤ %s | 🛡 %s | 💣 %s |❗%s » %s\n" % (_z(_max[0][_HP], 3), _z(_max[0][_DEF], 2), _z(_max[0][_DMG], 2), _z(_max[0][_CRT], 2)+'%', names[0])
        msg += "❤ %s | 🛡 %s | 💣 %s |❗%s » %s\n" % (_z(_max[1][_HP], 3), _z(_max[1][_DEF], 2), _z(_max[1][_DMG], 2), _z(_max[1][_CRT], 2)+'%', names[1])
        msg += "▬▬▬▬▬▬▬▬✩▬▬▬▬▬▬▬▬\n"
        msg += "» 💪 %s ❤ %.1f (🏆%d+%d%s) %s\n" % (names[1], pl[1][_HP], s[1]["pts"], pts[1], str_streak, data["used"][1])
        msg2 = "» ☠ %s (🏆%d%s 💢%d+%d) %s\n" % (names[0], s[0]["pts"], str_pts, s[0]["wrath"], wrath, data["used"][0])
        if not simulator:
            s[1]["pts"]    += pts[1]
            s[1]["wins"]   += 1
            s[1]["count"]  += 1
            s[1]["streak"] += streak[1]
            s[0]["pts"]    += pts[0]
            s[0]["wrath"]  += wrath
            s[0]["count"]  += 1
            s[0]["streak"] = streak[0]
            # Выдадим предметы
            msgs = ["", ""]
            for i in [0, 1]:
                if data["p"][i][1] != 0:
                    msgs[i] = self.get_rnd_item(ids[i], names[i], s[i]["slots"], data["p"][i][0], data["p"][i][1])
                if data["msg"][i]:
                    msgs[i] += data["msg"][i]
            if msgs[1]:
                msg += msgs[1]
            msg += msg2
            if msgs[0]:
                msg += msgs[0]
        else:
            msg += '\n' + self.print_moves()
        return [msg, data["cd"]]

    def get_rnd_item(self, _id, name, s, p_item, rnd):
        slot, item = self._random_item(p_item, rnd)
        return self._on_item(_id, name, s, slot, item)

    def _on_item(self, _id, name, s, slot, item):
        if slot is not None and item is not None:
            if slot in s:
                a = _on_choice_action(s[slot], item)
                if a == 0 and len(s[slot]) == 5:
                    a = -1
                if a == -1:
                    self._task.append_item(_id, name, slot, item, self._on_timer_item)
                    u_item = list(s[slot])
                    self.upgrade_item(u_item, item[1])
                    msg  = "[У]%s %s\n" % (self._act[1], self._print_item(1, slot, s[slot], u_item))
                    msg += "[З]%s %s\n" % (self._act[0], self._print_item(0, slot, item, s[slot]))
                    return msg
                return self.__on_item(s, slot, item, a)
            else:
                s[slot] = item
                return "%s %s\n" % (self._act[2], self._print_item(2, slot, item))
        return ""

    def __on_item(self, s, slot, item, is_upg, info=True):
        last = list(s[slot])
        if is_upg:
            self.upgrade_item(s[slot], item[1])
            return "%s %s\n" % (self._act[is_upg], self._print_item(is_upg, slot, last, s[slot]))
        else:
            s[slot] = item
            if not info:
                is_upg = 2
            return "%s %s\n" % (self._act[is_upg], self._print_item(is_upg, slot, s[slot], last))


# ======== ========= ========= ========= ========= ========= ========= =========
def calc_stats(slots, p, epl):
    crt = 100
    for item in slots:
        if slots[item][3] < 0:
            epl[slots[item][2]] += slots[item][3]
        elif slots[item][2] == _CRT:
            crt -= crt*(slots[item][3]/100)
        else:
            p[slots[item][2]] += slots[item][3]
    p[_CRT] = 100-crt


def _on_choice_action(old, new):    # -1 предложить заменить; 0 - заменить; 1 - улучшить
    """ old[3] > 0:     return f(0, 0, -1, -1, 1,  1)
        old[3] == 0:    return f(0, 0, -1,  0, 0, -1)
        old[3] < 0:     return f(-1, 1,  1,  0, 0, -1) """
    if old[0] == new[0]:
        return 1
    if old[2] != new[2] or (old[3] > 0 > new[3]) or (old[3] < 0 < new[3]):
        return -1
    if new[3] > old[3]:
        if new[1] > old[1]:
            return -int(old[3] < 0)
        elif new[1] == old[1]:
            return int(old[3] < 0)
        return -1+2*int(old[3] < 0)
    elif new[3] == old[3]:
        return int(new[1] <= old[1])
    else:
        if new[1] > old[1]:
            return -int(old[3] > 0)
        elif new[1] == old[1]:
            return int(old[3] > 0)
        return -1+2*int(old[3] > 0)


def _is_mod(mods, name):
    if name in mods and mods[name][0]:
        _dec(mods[name])
        return True
    return False


def _is_mod_rnd(m, name, rnd):
    if name in m:
        if random.random()*100 <= rnd:
            _dec(m[name])
            return True
    return False


def _dec(m):
    if m[1] == 0:
        m[0] -= 1
    m[1] += 1


def is_exchange(mods, index):
    m0, m1 = _is_mod(mods[0], index), _is_mod(mods[1], index)
    return not (m0 and m1) and m0 or m1


def _dmg(pl, attacker, scatter):
    k, is_crit = 1, False
    if random.random()*100 <= pl[attacker][_CRT]:
        k, is_crit = pl[attacker][_CRT_DMG], True
    d = (pl[attacker][_DMG]*k) - pl[not attacker][_DEF]
    dmg = random.uniform(d*scatter[0], d*scatter[1])
    if dmg < 1:
        dmg = 1
    return dmg, is_crit


def _on_skip_move(m, a):
    if "Везунчик" in m[a]:
        _dec(m[a]["Везунчик"])
        return True
    return False


def _get_player_mods(p):
    _list = list(p["mods"])
    for slot in p["slots"]:
        if len(p["slots"][slot]) == 5:
            _list += [p["slots"][slot][4]]
    return _list


def _invert_list(a, b):
    _list = []
    for e in b:
        if e not in a:
            _list += [e]
    return _list


def _reverse(pl, m, s, ids, nicknames, k):
    pl.reverse()
    m.reverse()
    s.reverse()
    nicknames.reverse()
    ids.reverse()
    k[0], k[1] = k[1], k[0]
    k[2].reverse()


def _print_cooldown(cooldown, _id):
    if _id in cooldown:
        return " [" + print_time(cooldown[_id]) + ']'
    return ""


def _generate_captcha():
    min_x, max_x, min_y, max_y, sym = -150, 150, -150, 150, '+'
    ans, text = 0, ""
    rnd = random.randint(0, 9)
    if rnd in [1, 5]:
        sym = '-'
    elif rnd in [2, 7, 8]:
        min_x, max_x = 3, 10
        min_y, max_y = 3, 10
        sym = '*'
    elif rnd in [4, 6, 9]:
        min_x, max_x = 2, 10
        min_y, max_y = 1, 3
        sym = '^'
    x = random.randint(min_x, max_x)
    y = random.randint(min_y, max_y)
    if rnd in [0, 3]:
        ans = x + y
    elif rnd in [1, 5]:
        ans = x - y
    elif rnd in [2, 7, 8]:
        ans = x * y
    elif rnd in [4, 6, 9]:
        ans = x ** y
    if y < 0:
        if sym == '-':
            sym = '+'
            y *= -1
        else:
            sym = ''
    text = "%d%s%d = ?" % (x, sym, y)
    rnd = random.randint(0, 2)
    if rnd == 1:
        z = random.randint(1, len(str(abs(ans))))
        text += " (Напишите " + str(z) + " цифру)"
        ans = int(str(abs(ans))[z-1])
    elif rnd == 2:
        text += " (Напишите сумму цифр ответа)"
        z = 0
        for c in str(abs(ans)):
            z += int(c)
        ans = z
    # print(ans)
    return ans, text
