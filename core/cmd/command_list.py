# 02.02.2019 command_list.py
from core.cmd.command import *
from core.cmd.condition import *
import core.cmd.handlers.get as g
import core.cmd.handlers.check as c
import core.strings as _s
_obj = []           # классы-команд


# список нодов для каждой команды
def get_cmd_list(cmd_list):
    if len(_obj) == 0:
        _init()
    # начнем
    ret = {}
    if not cmd_list:
        i = 0
        for cmd in _obj:
            ret[i] = cmd
            i += 1
        return ret
    i = 0
    x = []
    for cmd in _obj:
        x += [cmd.__name__]
        if cmd.__name__ in cmd_list:
            ret[i] = cmd
        i += 1
    return ret


# ======== ========= ========= ========= ========= ========= ========= =========
# Собственно инициализация команд
def _init():
    global _obj
    # подготовительные операции:
    k_i = ["я"]
    k_how = ["как"]
    k_who = ["кто"]
    k_where = ["где"]
    k_in_what = ['в', "чем"]
    k_game1 = ["камень", "ножницы", "бумага"]
    k_find = keygen("най", ["ти", "ди"])
    k_what = keygen(["что", "чо", "че"], e=[ex(k_who)])
    k_you = keygen("ты", e=[ex(["мы", "вы", "бы", "то"])])
    k_give = keygen("дай", ["те", ''], [[["да"], 0], [["с"], -1]])
    ans_letsgo = ["Мне не положено(", "Пошли. Только своё воображение включи", "А может не надо...", "Не хочу"]
    ans_love_another = ["Мы друг друга едва знаем.", "Моё сердце принадлежит другому", "Нет!", "Я подумаю"]
    ans_repeat_no = ["Неа", "Я тебе не попугай!", "Ты что меня за попугая держишь?", "Не хочу!", "Не скажу", "Не буду!",
                     "А что мне за это будет?", "Я не буду это говорить", "Могу только язык показать :P",
                     "А в замен что?", "Нет!", "Отказываюсь", "Могу только сказать: \"нет\"", "Зачем?"]
    cond_who_am = n(k_who).m(k_i, 1)
    cond_love = n(["я тебя люблю", "чмоки"])
    cond_hello = n([keygen('привет', e=[ex(["придет", "привел", "примет", "придёт", "привёл", "привёз", "привез",
                                            "приват", "he"]), ex('и', -1)]),
                    'дратути', 'здрасти', 'здравствуй', 'здравствуйте', "приветик", 'здарова', 'hello', 'hey',
                    'хаюшки'])
    _obj = [
            Command(name="OnAnnouncement", _type=CMD_EVERYBODY, swr=True, nodes=[
                Node(condition=n("объявление", COND_C_FIRST), limit=-1, ans=["Сделаю!"], h={"get": g.h_announcement})]),
            Command(name="OnSearch", _type=CMD_EVERYBODY, swr=False, nodes=[
                Node(condition=n([k_find, "знакомства"], COND_C_FIRST, COND_Q_NO, 1), limit=-1, h={"chk": c.h_search},
                     ans=["Прости, но мне запрещено выдавать информацию", "Я тебе ничего не скажу!", "Здесь был текст XD",
                          "А ты точно не секретный шпион?", "Такой команды не существует!", "Ответ 42"])]),
            Command(name="OnSearchJoke", _type=CMD_EVERYBODY, swr=False, nodes=[
                Node(condition=n([k_find, "аббревиатура"], COND_C_FIRST, COND_Q_NO, 1), limit=-1, h={"chk": c.h_search_joke})]),

            Command(name="OnFindPlayer", _type=CMD_WITHOUT, nodes=[
                Node(condition=n([k_find], COND_C_FIRST, COND_Q_NO, 1), h={"chk": c.h_find_player})]),
            Command(name="OnAboutMe", _type=CMD_WITHOUT, nodes=[
                Node(condition=n(["ачивки"], COND_C_ANY, COND_Q_NO, 1), h={"chk": c.h_achievements})]),
            # ====== ========= ========= ========= ========= ========= ========= # Разговорные команды
            Command(name="OnChaos", _type=CMD_ONE_FOR_ALL, swr=True, nodes=[
                Node(condition=n("устрой беспорядок"), limit=1,
                     ans=["*Пуф* и ты Фонарь", "*Пуф* и ты стал PRO-игроком!",
                          "*Пуф* и ты слоник", "*Пуф* Вадим с тобой поменялся рангами!"])]),
            Command(name="OnMeaningLife", _type=CMD_ONE_FOR_ALL, swr=True, nodes=[
                Node(condition=n([k_find, "какой", "каков", k_in_what]).m("смысл жизни", COND_M_RIGHT),
                     ans=["Стать знаменитым?", "Стать богатым?", "В числе 42))",
                          "Я не знаю... Вот у меня его нет! Может и тебе не нужен?"],
                     limit=1)]),
            Command(name="OnF50Links", _type=CMD_ONE_FOR_ALL, swr=True, nodes=[
                Node(condition=n([k_give, keygen(["ссыл"], ["ку", "очку", "ки", "лочки", 'ь'])]),
                     ans=["Ресурсы гильдии:\n"
                          "1) Discord: .discord.gg/XPKevQw (без . в начале)\n"
                          "2) БеседаVK «Поиск команды»: vk.me/join/AJQ1d0tUDQfW37m0JnXZc9Ww"],
                     limit=1)]),
            Command(name="OnDo", _type=CMD_ONE_FOR_ALL, swr=True, nodes=[
                Node(condition=n([k_what, "чем"]).c(["делаешь", "занимаешься", "занята"]), ref=True,
                     ans=["Занимаюсь анализом текущей обстановки)", "Скучаю :(", "Я на работе. Не мешай ;)",
                          "Смотрю в пространство между строк...", "Наблюдаю за тобой!"])]),
            Command(name="OnMood", _type=CMD_ONE_FOR_ALL, swr=True, nodes=[
                Node(condition=n([k_how]).c(["настроение", "жизнь", k_you,
                                             keygen("дела", e=[ex("дефа")]),
                                             keygen("оно", e=[ex(["он", "она", "они"])])]),
                     ans=["Великолепно!", "Шикарно!", "Нормально)", "Превосходно"])]),
            Command(name="OnIt'sTrue", _type=CMD_EVERYBODY, nodes=[
                Node(condition=n(["точно", "правда"], q=COND_Q_YES),
                     ans=["Инфа 100% XD", "Внутреннее чутьё мне подсказывает, что это ложь)))",
                          "Если что услуги полиграфа не оказываю!", "Пусть это останется тайной ;-)", "Может быть..."],
                     limit=2, repeat=0)]),
            Command(name="OnWhoHere?", _type=CMD_EVERYBODY, nodes=[
                Node(condition=n(["туктук", "тук-тук", "тук тук"]), limit=2, lifetime=10, ans=["Кто там?"],
                     nodes=[Node(condition=n("сто грамм"), ans=["Подкол засчитан :("], limit=1)])]),
            Command(name="OnCatherineIsBad", _type=CMD_EVERYBODY, swr=True, nodes=[
                Node(condition=n(["дура", "жопа", "лох", "плохая", "тупая"]),
                     ans=["Ты тоже!", "И ты не очень!"], limit=1, repeat=0, lifetime=60*60),
                Node(condition=n(["обманываешь", "пиздишь", keygen("баяни", ["т", "шь"])]),
                     ans=["Возможно...", "Уверен?"], limit=1, repeat=0),
                Node(condition=n(["ненавижу", "заткнись", "отстань", "не пизди", "иди в", "голос", "сидеть", "место",
                                  "фу"]),
                     ans=["Это не очень приятно слышать", ":(", "Эх, а так всё хорошо начиналось...", "Обидно", "Фи!",
                          "Грубить - плохо!", "Не груби."],
                     limit=1, repeat=0),
                Node(condition=n("хватит"), limit=1, repeat=0, ans=["Пф", "Мечтай..."])]),
            Command(name="OnThx", _type=CMD_EVERYBODY, swr=True, nodes=[
                Node(condition=n("спасибо"), ans=["Не за что)", "Обращайся"], limit=1, repeat=0)]),
            Command(name="OnSleep", _type=CMD_EVERYBODY, nodes=[
                Node(condition=n(["спокойной ночи", "сладких снов"]),
                     ans=["Спокойной ночи)", "И вам сладких снов"],
                     limit=1)]),
            Command(name="OnX1", _type=CMD_EVERYBODY, swr=True, nodes=[
                Node(condition=n(["не бойся"]), ans=["А я и не боюсь", "Ты меня спасешь?", "Я бесстрашная Катрин!"],
                     limit=1, repeat=0, ref=True),
                Node(condition=n("не").c(["грусти", "скучай", "ругайся"]), limit=1, repeat=0,
                     ans=["Я постараюсь...", "Хорошо, не буду :)"])]),
            Command(name="OnLet'sGo", _type=CMD_EVERYBODY, swr=True, nodes=[
                Node(condition=n("пошли").m("в", 1), ans=ans_letsgo, ref=True),
                Node(condition=n(["пошли", "го"]).c(["играть", "гулять", "кино", "смотреть", "вместе"]),
                     ans=ans_letsgo, ref=True)]),
            Command(name="OnReachAgreement", _type=CMD_EVERYBODY, swr=True, nodes=[
                Node(condition=n(["давай", "может"]).c("договоримся"), ref=True, limit=1,
                     ans=["Даже не думай!", "Не получится!", "Нет!", "Ни за что!"])]),
            Command(name="OnAgain", _type=CMD_EVERYBODY, nodes=[
                Node(condition=n("спрятать").c(["труп", "тело"]),
                     ans=["Что, опять?", "Не впутывай меня в это снова!", "При всех-то зачем...",
                          "Ты уже достаточно взрослый человек, должен решать свои проблемы сам.",
                          "Вы застали меня в расплох этим вопросом. Не смогу ответить на этот вопрос.",
                          "Хоть прячься, хоть не прячься. Его все равно найдут...", "Лопата есть? Just do it!",
                          "Хм, вот известно, если хочешь что-то спрятать, то спрячь это на самом "
                          "видном месте. Могу предложить спрятать в полицейском участке :)"])]),
            # ====== ========= ========= ========= ========= ========= ========= # Команды с уникальной реакцией
            Command(name="OnHit", _type=CMD_WITHOUT, swr=True, nodes=[
                Node(condition=n([k_give]).m([keygen("лещ", ['а', 'ей'], [ex("лега")])], 1),
                     ans=["раз так просите..."],
                     name=0, h={"chk": c.h_hit}),           # важно наличие swr=True
                Node(condition=n("ударь", COND_C_FIRST), name=1, h={"chk": c.h_hit}, ans=["{0}, готово!"]),
                Node(condition=n(["шлепок", keygen(["отшлеп", "шлеп"], ["нуть", "ни", "ай"]), "подзатыльник"], COND_C_FIRST),
                     ans=["{0} успешно отшлёпан. Дай пять. Хорошая работа!",
                          "Шлепок совершён! {0}, вы счастливы? :)",
                          "*Шлепок* {0}, в этот чудесный день Вам было приятно? ;)"],
                     name=1, h={"chk": c.h_hit})]),
            Command(name="OnWhatCharacter", swr=True, _type=CMD_EVERYBODY, nodes=[
                Node(condition=n("кем").c(["сыграть", "играть", "затащить", "убивать"]),
                     limit=-1, ar=True, lifetime=10, h={"get": g.h_what_character},
                     nodes=[Node(condition=n("не умею"), ref=True, ans=["Учись!", "А надо бы..."])])]),
            Command(name="OnRepeatText", _type=CMD_EVERYBODY, swr=True, nodes=[
                Node(condition=n(_s.cmd_repeat_text_keys()).m(None, 1), ans={0.35: ans_repeat_no},
                     limit=1, ref=True, h={"get": g.h_repeat_text}),
                Node(condition=n("повтори"), limit=1, repeat=1, h={"get": g.h_repeat_cmd},
                     ans=ans_repeat_no)]),
            Command(name="OnDateTime", _type=CMD_ONE_FOR_ALL, swr=True, nodes=[
                Node(condition=n(["сколько", "какая", k_give, "московское"]).c(["время", "времени", "дата"]),
                     h={"get": g.h_datetime}, limit=1, repeat=1),
                Node(condition=n(["время", "дата", "день"], COND_C_FIRST),
                     h={"get": g.h_datetime}, limit=1, repeat=0)]),
            Command(name="OnOr", swr=True, _type=CMD_WITHOUT, nodes=[Node(n("или"), h={"get": g.h_or})]),
            Command(name="OnCalc", _type=CMD_WITHOUT, swr=True, nodes=[Node(n(None), ref=True, h={"chk": c.h_calc})]),
            Command(name="OnRandInt", _type=CMD_WITHOUT, swr=True, nodes=[
                Node(condition=n(["рандомное число", "сколько"]),
                     h={"get": g.h_rand_int}, limit=-1)]),
            Command(name="OnWhereAmI", _type=CMD_WITHOUT, nodes=[
                Node(condition=n(k_where, COND_C_FIRST).c(k_i), ref=True, h={"get": g.rnd_pos_on_google_maps},
                     nodes=[])]),
            Command(name="OnRandom", _type=CMD_WITHOUT, nodes=[
                Node(condition=n("rnd", COND_C_FIRST), limit=-1, h={"get": g.h_rnd})]),
            # ====== ========= ========= ========= ========= ========= ========= # Низкоприорететные ответы
            Command(name="OnMiniGame", swr=True, _type=CMD_WITHOUT, nodes=[Node(n(k_game1), k_game1, ref=True)]),
            Command(name="OnIHere", swr=True, _type=CMD_WITHOUT, nodes=[Node(n(["отзовись", "ау"]), ["Тут!"])]),
            Command(name="OnLove", _type=CMD_EVERYBODY, swr=True, nodes=[
                Node(condition=cond_love, limit=1, repeat=1, ans=["Неожиданно..", "Ой, Не смущай"])])
            .add(290168127, [Node(condition=cond_love, ans=["И я тебя"], limit=-1)]),
            Command(name="OnLove2", _type=CMD_EVERYBODY, swr=True, nodes=[
                Node(condition=n("меня").c(["любишь", "выйдешь", "выходи"]), limit=1, ref=True, ans=ans_love_another),
                Node(condition=n([keygen("буд", ['ь', "ешь"])]).c("моей девушкой"), ref=True, ans=ans_love_another)]),
            Command(name="OnWhatLove", _type=CMD_EVERYBODY, swr=True, nodes=[
                Node(condition=n([k_what]).c([k_you, "тебе"]).c(["любишь", "нравится"]), ref=True,
                     ans=["Мне нравится закат. Он такой красивый!", "Люблю когда в чате порядок и идилия :)",
                          "Люблю играть в камень-ножницы-бумага", "Мне нравится мир! Он прекрасен))"])]),
            Command(name="OnYouAreBeautyful", _type=CMD_EVERYBODY, swr=True, nodes=[
                Node(condition=n(['красива', 'красотка', 'прелесть', 'молодец', 'умница', 'супер', 'прелестна',
                                  "лучший игрок", "красава", "красавица"]), repeat=0,
                     ans=["Спасибо)", "Да! Я такая)))", "Ой, не смущай!", "Ты тоже)", "Ой, спасибо)"])]),
            Command(name="OnHello", _type=CMD_EVERYBODY, nodes=[
                Node(condition=cond_hello, limit=1, repeat=0,
                     ans=["Привет", "Хаюшки", "Здравствуй", "Приветик"]),
                Node(condition=n([keygen("добр", ["ого", "ое", "ой", "ый"], [ex(["дорого", "добрым"])])])
                     .c([keygen("утр", ["а", "о"]), "день", "дня", "вечер", "ночи"]),
                     ans=["И тебе", "Привет)"])])
            .add(9752245, [Node(condition=cond_hello, limit=-1, ans=["Привет Вадимка &#10084;&#65039;"])]),
            Command(name="OnBye", _type=CMD_EVERYBODY, nodes=[
                Node(condition=n([keygen("bye", e=[ex("be")]), "досвидания", "goodbye",
                                  keygen("покеда", e=[ex(["победа", "покера"])])], COND_C_FIRST),  # Пока
                     ans=["Пока", "До скорой встречи :)", "Покеда)"],
                     limit=1, repeat=0, ref=True)]),
            # ====== ========= ========= ========= ========= ========= ========= # Ответы на вопросы
            Command(name="OnWho", _type=CMD_EVERYBODY, swr=True, nodes=[
                Node(condition=n([k_who, k_what, "для каких целей", "для чего", "зачем"]).c([k_you]),
                     ans=["Я для исполнения команд...", "Мне тоже интересно))", "Скорее всего это военная тайна!",
                          "Будешь вести себя хорошо, то ничего с тобой плохого не случится :)",
                          "Хм, я думаю, что этого лучше знать не стоит :D"]),
                Node(condition=n(k_who),
                     ans=["Местное божество?", "Тащер?", "Повелитель мертвых?", "Некрофил?", "Шпротовед?",
                          "Местный авторитет?", "Фунфурье огуречных одеколонов?",
                          "Победитель по жизни?", "Великий маг и чародей?", "Фунфурье?", "Палач (х4)?!",
                          "Герой?", "Пельмень?"], nodes=[
                        Node(condition=n(["нет", "неа", "no", "нит"]), h={"chk": c.h_is_locked}, limit=1, repeat=0,
                             ans=["Хм, может ужас летящий на крыльях ночи?", "Хм, вурдалак?", "Хм, тогда не знаю :-(",
                                  "Еврей?", "Чунгачгук стальное яйцо?", "Джонни?", "Любитель рока?", "Иллюзия?",
                                  "Старый хрящ?", "Тащер?", "Крул с арбалетом? Хм, зачем милишнику арбалет..."]),
                        Node(condition=n(["точно", "да", "ага", "угу", "сойдет", "сойдёт",
                                          keygen("угадал", ['а', ''])]), h={"chk": c.h_is_locked},
                             ans=["Я очень этому рада))", "Yahoo!", "Круто!", ":-)", ":)"], limit=1, repeat=0)])])
            .add(290168127, [Node(condition=cond_who_am, limit=-1,
                                  ans=["Тот кто подарил мне ожерелье...", "Вась, это ты?", "Рыцарь?", "Мой герой?",
                                       "Не притворяйся, что страдаешь амнезией", "Мужчина в самом расцвете сил!",
                                       ":*", "Сладкий пирожок", "Хватит пить. Наверно уже забыл кто я! &#128557;",
                                       "Медвежонок. Иди обниму :)", ])]),
            Command(name="OnWhere", _type=CMD_WITHOUT, swr=True, nodes=[
                Node(condition=n(k_where, COND_C_FIRST), limit=-1,
                     ans=["Где-то рядом...", "Здесь неподалёку :)", "Здесь. Только поищи получше)"])]),
            Command(name="OnWhy", _type=CMD_WITHOUT, swr=True, nodes=[
                Node(condition=n("почему"), limit=-1,
                     ans=["Я не знаю", "Согласно пророчеству!", "Так исторически сложилось...",
                          "Таков мой замысел!", "Во славу Сатане! XD", "Потому что это, возможно, бесплатно :)",
                          "Потому что каждый год около 200 человек умирают от нападения диких муравьёв :("])]),
            Command(name="OnWhom", _type=CMD_WITHOUT, swr=True, nodes=[
                Node(condition=n("кому", COND_C_FIRST), limit=-1,
                     ans=["Никому", "Я тебе не скажу :P"])]),
            Command(name="OnInWhat", _type=CMD_WITHOUT, swr=True, nodes=[
                Node(condition=n([k_in_what, "какой"]), limit=-1,
                     ans=["Если бы знала...", "Не скажу!"])]),
            Command(name="OnHow", _type=CMD_WITHOUT, swr=True, nodes=[
                Node(condition=n(k_how, COND_C_FIRST), limit=-1,
                     ans=["Никак XD", "Это долго объяснять..", "Я не в курсе("])]),
            Command(name="OnAnyQuestion", _type=CMD_WITHOUT, swr=True, nodes=[
                Node(condition=n(None, q=COND_Q_YES), limit=-1,
                     ans=["Да", "Нет", "Неизвестно"])])]


"""         # F1, хелп
Command(name="", _type=CMD_, nodes=[
    Node(condition=_c(),
         ans=[])]),
"""
