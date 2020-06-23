# 16.02.2019
import random


HR_CAPTAIN = "капитан"
HR_JUNGLER = "лесник"
HR_LINER = "лейнер"
HR_ERROR = "неизвестная роль"


def get_hero_data():
    res = dict()
    res[HR_CAPTAIN] = [["Adagio", "Адажио"], ["Ardan", "Ардан"], ["Catherine", "Катрин"],
                       ["Churnwalker", "Чернвокер"], ["Flicker", "Фликер"], ["Fortress", "Фортресс"],
                       ["Grace", "Грейс"], ["Lance", "Ланс"], ["Lorelai", "Лорелея"], ["Lyra", "Лира"],
                       ["Phinn", "Финн"], ["Yates", "Йейтс"]]
    res[HR_JUNGLER] = [["Alpha", "Альфа"], ["Glaive", "Глейв"], ["Grumpjaw", "Грамп"], ["Inara", "Инара"],
                       ["Joule", "Джоуль"], ["Koshka", "Кошка"], ["Krul", "Крул"], ["Ozo", "Озо"],
                       ["Petal", "Петаль"], ["Reim", "Рейм"], ["Rona", "Рона"], ["Ylva", "Ильва"], ["Taka", "Така"],
                       ["Tony", "Тони"]]
    res[HR_LINER] = [["Sanfeng", "Сань Фен"], ["Anka", "Анка"], ["Baptiste", "Батист"], ["Baron", "Барон"],
                     ["Blackfeather", "Ворон"], ["Celeste", "Селеста"], ["Gwen", "Гвен"], ["Idris", "Идрис"],
                     ["Kensei", "Кенсей"], ["Skaarf", "Скаарф"], ["Skye", "Скай"], ["Kestrel", "Кэстрел"],
                     ["Kinetic", "Кинетика"], ["Magnus", "Магнус"], ["Malene", "Малена"], ["Reza", "Риза"],
                     ["Ringo", "Ринго"], ["Samuel", "Сэмюэль"], ["SAW", "П.И.Л.А."], ["Silvernail", "Сильвернейл"],
                     ["Varya", "Вайра"], ["Vox", "Вокс"]]
    return res


def translate(obj, name, ru):
    for role in obj:
        for hero in obj[role]:
            if (ru and hero[0] == name) or (not ru and hero[1] == name):
                return hero[ru]
    return HR_ERROR


def rnd(ru):
    obj = get_hero_data()
    items = obj[HR_LINER] + obj[HR_JUNGLER] + obj[HR_CAPTAIN]
    index = random.randint(0, len(items)-1)
    return items[index][ru]


def rnd_role():
    role = [HR_CAPTAIN, HR_JUNGLER, HR_LINER]
    return role[random.randint(0, 2)]


def get_hero_role(name, ru=False):
    obj = get_hero_data()
    for role in obj:
        for hero in obj[role]:
            if name in hero[ru]:
                return role
    return HR_ERROR

