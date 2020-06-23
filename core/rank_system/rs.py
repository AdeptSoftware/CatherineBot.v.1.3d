import re
import core.rank_system.any_cond as _c
import core.instance


# измеряется в словах
rank_list = [["Неизвестный", 0],                                    # 0
             ["Тень", 50],                                          # 1
             ["Усердный", 400],                                     # 2
             ["Исследователь", 1000],                               # 3
             ["Печатная машинка", 2000],                            # 4
             ["Словарь", 4000],                                     # 5
             ["Эрудит", 8000],                                      # 6
             ["Библиотекарь", 13500],                               # 7
             ["Оратор", 20000],                                     # 8
             ["Эксперт", 25000],                                    # 9
             ["Хранитель мудрости", 37500],                         # 10
             ["Великий жрец", 50000],                               # 11
             ["Владыка", 70000],                                    # 12
             ["Легенда чата", 100000],                              # 13
             ["Сверхразум", 200000],                                # 14
             ["Сама бесконечность", 1000000000]]


def print_achievement(mp, index, current_value, _all=False):
    key, value = 0, None
    for a_key in _c.achievement_list[index][1]:
        if a_key <= current_value:
            key = a_key
        else:
            if _all:
                value = [current_value, a_key]
            break
    if key == 0:
        return ""
    if not value and _all:
        value = [current_value, list(_c.achievement_list[index][1].keys())[-1]]
    return _c.print_achievement(mp, index, key, value, False, True)


def _length(_list, max_count, _ex):
    for e in _list:
        if not e.isnumeric() and e not in _ex and len(e) > max_count:
            print(e)
            return False
    return True


def main(mp, spam_count=5, spam_time=60):
    if mp.uid in [18157007]:
        return True

    # Если повторяется текст, то не учитываем
    if mp.s["last"][0] == mp.item["text"]:
        mp.s["last"][1] += 1
        if mp.s["last"][1] == spam_count and mp.s["last"][2] < spam_time:
            mp.send("тебе не кажется, что это уже спам?!")
        mp.s["last"][2] = mp.item["date"]
        return True
    # Построим частоту употребления слов
    f = {}
    for w in mp.words:
        if w[1] in f:
            f[w[1]] += 1
        else:
            f[w[1]] = 1
    msg = ""
    if len(f) != 0:
        x = sorted(f.items(), key=lambda kv: kv[1])
        x.reverse()
        for k in x:
            if len(k[0]) >= 3 and f[k[0]] > 3:
                # msg += "→ Знаешь.. В этом сообщении слово «" + k[0] + "» встречается " + str(k[1]) + " раз(-а)?\n"
                break
    r0 = re.compile(r"\s+")
    r1 = re.compile(r"[a-z]")
    r2 = re.compile(r"[аеёиоуыэюя]")
    r3 = re.compile(r"[бвгджзйклмнпрстфхчцшщ]")
    count = len(mp.words)
    word_count = 0
    for i in range(0, count):
        length = len(mp.words[i][1])
        if r1.search(mp.words[i][1]) is not None or \
           not _length(r0.split(r2.sub(' ', mp.words[i][1]).strip()), 3, ["ств", "нстр", "встр", "льств", "йств",
                                                                          "нств", "тств", "вств", "взгл", "рств",
                                                                          "ссср"]) or \
           not _length(r0.split(r3.sub(' ', mp.words[i][1]).strip()), 2, []) or \
           (f[mp.words[i][1]] <= 3 and (length < 3 or length > 12)):
            continue
        mp.s["symbol"] += length
        word_count += 1
    mp.s["word"][0] += word_count
    # Обновим статы и проверим выполняются ли достижения
    for i in range(0, len(_c.achievement_list)):
        if _c.achievement_list[i][0] is not None:
            if callable(_c.achievement_list[i][0]):
                msg_x = _c.achievement_list[i][0](mp)
                if msg_x != "":
                    msg += "→ " + msg_x
            else:
                if _c.achievement_list[i][0].check(mp, lambda: True):
                    msg_x = _c.inc(mp, i)
                    if msg_x != "":
                        msg += "→ " + msg_x
    # Теперь ранги
    if mp.s["rank"]+1 < len(rank_list) and mp.s["word"][0] >= rank_list[mp.s["rank"]+1][1]:
        mp.s["rank"] += 1
        _s = ""
        if not mp.is_man:
            _s = 'а'
        msg += "→ " + mp.ref(True) + " получил" + _s + " новый ранг «" + rank_list[mp.s["rank"]][0] + "»\n"
    # всегда должно быть в конце:
    mp.s["last"] = [mp.item["text"], 1, mp.item["date"]]
    if msg != "":
        mp.send(msg)
    return True
