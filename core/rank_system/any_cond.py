# 21.07.2019
import core.cmd.condition as _x
import core.instance


def print_achievement(mp, index, key, value=None, description=True, only_name=False):
    if key in achievement_list[index][1]:
        _s = ""
        if mp is not None and not mp.is_man:
            _s = 'а'
        msg = ""
        if not only_name:
            if mp is not None:
                msg += mp.ref(True)
            msg += " получил" + _s + " достижение "
        msg += "«" + achievement_list[index][1][key][0] + "» ("
        if value is not None:
            msg += str(value[0]) + '/' + str(value[1])
        else:
            msg += str(key)
        msg += ')'
        if description and achievement_list[index][1][key][1] is not None:
            import random
            i = random.randint(0, len(achievement_list[index][1][key][1])-1)
            msg += "\n„"+achievement_list[index][1][key][1][i]+'“'
        return msg + '\n'
    return ""


def inc(mp, index):
    if index in mp.s["achievements"]:
        mp.s["achievements"][index] += 1
        return print_achievement(mp, index, mp.s["achievements"][index])
    else:
        mp.s["achievements"][index] = 1
    core.instance.app().eventer.update_event_data("data_updater", "flag", True)
    return ""


def inc_s(mp, index, value):
    save_key = 0
    progress = None
    keys = tuple(achievement_list[index][1].keys())
    for i in range(0, len(keys)):
        if keys[i] <= value:
            save_key = keys[i]
            if i+1 == len(keys):
                progress = None
            else:
                progress = [value, keys[i+1]]
        else:
            break
    if save_key != 0:
        if index not in mp.s["achievements"] or mp.s["achievements"][index][0] < save_key:
            mp.s["achievements"][index] = [save_key, value]
            return print_achievement(mp, index, save_key, progress)
        else:
            if mp.s["achievements"][index][1] < value:
                mp.s["achievements"][index][1] = value
        core.instance.app().eventer.update_event_data("data_updater", "flag", True)
    return ""


def _cond_agent(mp):
    if mp.item["date"]-mp.s["last"][2] >= 604800:   # Больше недели
        return inc(mp, 6)
    return ""


def _cond_fast_msg(mp):
    if mp.item["date"]-mp.s["last"][2] <= 3:
        return inc_s(mp, 7, len(mp.item["text"]))
    return ""


def _cond_bracket(mp):
    flag = (')' in mp.prefix or (mp.length != 0 and ')' in mp.words[mp.length-1][2]))
    if not flag:
        for w in mp.words:
            if ')' in w[2]:
                flag = True
                break
    if flag:
        return inc(mp, 9)
    return ""


def __cond_att(mp, _id, _type, ext=None):
    for a in mp.item["attachments"]:
        if "type" in a and a["type"] == _type:
            if ext is None or a[_type]["ext"] == ext:
                return inc(mp, _id)
    return ""


def _cond_stickers(mp):
    return __cond_att(mp, 11, "sticker")


def _cond_butthurt(mp):
    if achievement_list[12][2].check(mp, lambda: True) or (mp.length > 1 and mp.item["text"].isupper()):
        return inc(mp, 12)
    return ""


def _cond_repost(mp):
    return __cond_att(mp, 13, "wall")


def _cond_symbol(mp):
    return inc_s(mp, 15, mp.s["symbol"])


def cond_duel_wins(wins, a):
    if wins in achievement_list[8][1] and (8 not in a or a[8] < wins):
        a[8] = wins
        core.instance.app().eventer.update_event_data("data_updater", "flag", True)
        return print_achievement(None, 8, wins)
    return ""


def _cond_smile(mp):
    for c in mp.item["text"]:
        if ord(c) > 8000:
            return inc(mp, 16)
    return ""


def _cond_gif(mp):
    return __cond_att(mp, 17, "doc", "gif")


def _cond_picture(mp):
    return __cond_att(mp, 19, "photo")


# достижения
# при добавлении достижения необходимо подправить кол-во их в yandex_disk.s_get
achievement_list = [[_x.n(["я", "меня", "мне"]),                                        # 0
                     {100: ["Эгоист",
                            ["Ваше «эго» никогда не было обделено вниманием",
                             "Любитель рассказать о себе",
                             "Эгоизм в крови"]]}],

                    [_x.n([_x.keygen("най", ["ти", "ди"])], _x.COND_C_FIRST,
                          _x.COND_Q_NO, 1),                                             # 1
                     {10: ["Активный пользователь",
                           ["Найду несмотря ни на что"]],
                      25: ["Любопытный", None],
                      50: ["Поисковый отряд",
                           ["Всегда в поисках окаменелостей",
                            "Докапавшийся до истины"]],
                      100: ["Разведчик", None],
                      250: ["Агент спецслужб", None]}],

                    [_x.n("где я", _x.COND_C_FIRST),                                    # 2
                     {10: ["Амнезия",
                           ["Путешествия по миру не прошли зря...",
                            "В первые в этих дебрях"]],
                      25: ["Невезучий путешественник",
                           ["Откуда мне только не пришлось выбираться по несколько раз..."]],
                      50: ["Опытный путешественник", None],
                      100: ["Опытный путещественник II", None],
                      250: ["Вокруг света",
                            ["Куда только судьба Вас не закидывала..."]]}],

                    [_x.n("кем").c(["сыграть", "играть", "затащить", "убивать"]),       # 3
                     {10: ["Рискованное дело",
                           ["Всегда готов к любым неожиданностям",
                            "Риск - дело благородное"]],
                      25: ["Отчаянный геймер",
                           ["Важны лишь прямые руки"]],
                      50: ["Отчаянный геймер II",
                           ["Всегда готов к любым неожиданностям"]],
                      200: ["Мастер на все руки", None],
                      500: ["Экстримал", None]}],

                    [_x.n(["дуэль", "пощечина"], _x.COND_C_FIRST),                      # 4
                     {5: ["Дело чести",
                          ["Рискуешь окончить жизнь как Пушкин",
                           "Астрологи объявлили неделю дуэлей. Цена на гробы выросла",
                           "Сегодня на одного покойника станет больше",
                           "Пощечина. В нашем стане еще один краснолицый...",
                           "Честь береги смолоду"]],
                      25: ["Дуэлянт",
                           ["То самое чувство, когда везенье на твоей стороне",
                            "Закаленный боями",
                            "Самая быстрая рука на всём Диком Западе"]],
                      50: ["Преследователь", None],
                      75: ["Преследователь II", None],
                      100: ["Кровожадный",
                            ["Еще не застыла кровь на губах"]],
                      250: ["Most wanted!",
                            ["За тобой уже выехали",
                             "Ваш взгляд заставляет содрогнуться"]],
                      500: ["Серийный убийца", None],
                      1000: ["Маньяк",
                             ["Безумие - это не предел",
                              "Дуэль с Вами - это игра в ящик",
                              "Кто не спрятался, я не виноват!"]],
                      1666: ["Сатана", None],
                      2500: ["Вселенское зло", None]}],

                    [_x.n([_x.keygen("кто")]).c(["играть", "катать"]),       # 5
                     {3: ["Всегда готов", None],
                      10: ["Попытка не пытка", None],
                      15: ["Капкан", None],
                      30: ["Опытный охотник",
                           ["Охота на крупную дичь"]],
                      50: ["Командир отряда",
                           ["Вы знаете толк в командной игре",
                            "Без Вас тиммейты - никто"]],
                      100: ["Полководец", None],
                      250: ["Генерал", None],
                      500: ["Генералиссимус", None]}],

                    [_cond_agent,                                                       # 6
                     {7: ["Тайный агент",
                          ["Шпион, молчавший длительное время, найден!"]]}],

                    [_cond_fast_msg,                                                    # 7
                     {300: ["Неудержимый", None],
                      500: ["Быстрее ветра", None],
                      800: ["Молниеносный", None],
                      1000: ["Сверхзвуковой", None],
                      1500: ["Повелитель времени", None],
                      3000: ["К бесконечности", None]}],

                    [None,                                                              # 8
                     {2: ["Двухкратный чемпион", None],
                      5: ["Пятикратный чемпион", None],
                      10: ["Уворотливая мишень", None],
                      25: ["Бронированный", None],
                      50: ["Мертвец", None],
                      75: ["Призрак", None],
                      100: ["Дух Дуэлей", None]}],

                    [_cond_bracket,                                                     # 9
                     {10: ["Капелька веселья", None],
                      25: ["Веселый роджер", None],
                      50: ["Железнодорожная скоба",
                           ["Был ограблен небольшой склад))"]],
                      100: ["Вагон и маленькая тележка))",
                            ["Когда и вагона мало..."]],
                      150: ["Промышленный размах I", None],
                      200: ["Промышленный размах II", None],
                      250: ["Промышленный размах III",
                            ["Потребители довольны)"]],
                      500: ["Скобкофилия",
                            ["Уже как заболевание..."]],
                      1000: ["Болезнь прогрессирует))) I", None],
                      2500: ["Болезнь прогрессирует)) II", None],
                      5000: ["Болезнь прогрессирует) III", None],
                      10000: ["В масштабах вселенной", None]}],

                    [_x.n(["ем", "пожру", "покушаю", "жрать", "кушать", "еда",          # 10
                           "пища", "еду", "пищу"]),
                     {5: ["Кулинар",
                          ["Вы знаете толк в еде"]],
                      15: ["Гурман",
                           ["Тебе так просто не угодишь)"]]}],

                    [_cond_stickers,                                                    # 11
                     {13: ["Чертова дюжина стикеров", None],
                      50: ["Актёр",
                           ["Сменить маску как два пальца..."]],
                      150: ["Эмоциональный", None],
                      500: ["Человек «Стикер»",
                            ["Это уже болезнь...",
                             "Для тебя жизнь без стикеров невозможна"]],
                      1000: ["Стикероапокалипсис", None],
                      2500: ["Стикероапокалипсис II", None],
                      5000: ["Стикероапокалипсис III", None]}],

                    [_cond_butthurt,                                                    # 12
                     {1: ["С огоньком",
                          ["Дело пахнет жареным"]],
                      10: ["В лепёшку!",
                           ["Уже начала подгорать..."]],
                      25: ["Реактивная тяга",
                           ["Ещё чуть-чуть и оторвётся от земли..."]],
                      40: ["30-тикратный чемпион по бомбёжке",
                           ["Первая ступень отделилась..."]],
                      61: ["Космонавт",
                           ["Достигший первой космической скорости"]],
                      100: ["Эксперт магии Огня", None]},
                     _x.n(["горю", "горит", "пылаю", "бомблю", "пылает", "дымит"])],

                    [_cond_repost,                                                      # 13
                     {5: ["Книжный червь", None]}],

                    [_x.n(["зачем сказал", "держи в курсе"]),                           # 14
                     {10: ["Молот справедливости", None]}],

                    [_cond_symbol,                                                      # 15
                     {666: ["Приспешник Дьявола", None],
                      5000: ["+5 к красноречию", None],
                      9000: ["Over 9000", None],
                      25000: ["Язык - друг мой, враг мой!", None],
                      50000: ["Находка для шпиона", None],
                      100500: ["100500", None],
                      500000: ["0,5 млн букв? Пф-ф-фигня!", None]}],

                    [_cond_smile,                                                       # 16
                     {25: ["Эмоции через край", None],
                      100: ["100 смайликов", None],
                      500: ["500 смайликов", None]}],

                    [_cond_gif,                                                         # 17
                     {15: ["GIF-Менеджер", None],
                      50: ["GIF-Мастер", None],
                      150: ["Властелин гифок", None]}],

                    [_x.n(["ор", "ору"]),                                               # 18
                     {10: ["Орк", None],
                      100: ["Оральный хор", None]}],

                    [_cond_picture,                                                     # 19
                     {5: ["Художник", None],
                      50: ["Художественная выставка", None],
                      150: ["Третьяковская галерея", None]}]]
