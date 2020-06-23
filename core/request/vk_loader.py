# 12.02.2019
from core.instance import *
import requests
import re

_nick = re.compile(r"\b[A-Za-z0-9_]{3,16}\b")
_domain = re.compile(r"\"pi_author\" href=\"/(.+)[\"\'] rel")
_topic_msg = re.compile(r"<div class=\"pi_text\">(.+)</div>")
domain_list = []

def replace_codes(text):
    return text.replace('&quot;', '?').replace('&amp;', '&').replace('&#33;', '!').\
        replace('&#036;', '$').replace('&#092;', '\\').replace('&gt;', '>').\
        replace('&lt;', '<').replace('<br/>', '\n').replace('</a>', '').replace('&#39;', '\'')

def replace_image(text):
    while "<img" in text:
        s0 = text.find("<img")
        s1 = text.find(">", s0)
        if s1 < 0:
            text = text[:s0]
        else:
            text = text[:s0]+text[s1+1:]
    return text

def find_comments(domain, offset=0, refresh=False):
    comments = []
    global domain_list
    if refresh or len(domain_list) == 0:
        refresh = True
    if not refresh:
        for i in range(0, len(domain_list)):
            if domain == domain_list[i]:
                res = requests.get("https://vk.com/topic-165091372_38081128", params={"offset": i})
                if res.status_code != 200:
                    break
                text = replace_codes(_topic_msg.findall(res.text)[0])
                comments += [replace_image(text)]
    while refresh:   
        res = requests.get("https://vk.com/topic-165091372_38081128", params={"offset": offset})
        if res.status_code != 200:
            break
        domains = _domain.findall(res.text)
        if (refresh):
            domain_list += domains;
        if len(domains) == 0:
            break
        if domain in domains:
            texts = _topic_msg.findall(res.text)
            if len(domains) != len(texts):
                app().log("Количество domain не совпадает с количеством ников!", domains+[None]+texts)
            else:
                comments += [replace_image(replace_codes(texts[domains.index(domain)]))]
        offset += 20
    return comments


# vk залочил доступ сообществам к методу board.getComments - теперь пытаемся обойти...
# topic_id = topic[group_id]_[topic_id]
def get_comments(topic_id, offset=0):
    res = requests.get("https://vk.com/"+topic_id, params={"offset": offset})
    if res.status_code == 200:
        domains = _domain.findall(res.text)
        texts = _topic_msg.findall(res.text)
        if len(domains) != len(texts):
            app().log("Количество domain не совпадает с количеством ников!", domains+[None]+texts)
        else:
            for i in range(0, len(texts)):     # <a href, <img
                texts[i] = replace_codes(texts[i])
                k = ""
                flag = True
                length = len(texts[i])
                for x in range(0, length):
                    if texts[i][x] == '<':
                        if (x+1 < length and texts[i][x+1] == "a") or (x+4 < length and texts[i][x+1:x+4] == "img"):
                            flag = False
                    if flag:
                        k += texts[i][x]
                    if texts[i][x] == '>':
                        flag = True
                texts[i] = k
            return domains, texts
    return None, None


# получить список ников
def get_nicknames(topic_list, group, ignore_words, is_all=True):
    user = {}
    for _id in topic_list:
        if is_all:
            offset = 0
        else:
            offset = app().get(_id, 0)
        while True:
            domains, texts = get_comments(_id, offset)
            if domains is None or texts is None:
                continue
            if len(domains) == 0:
                break
            offset += 20
            # получим ники
            for i in range(0, len(texts)):
                if domains[i] not in user:
                    user[domains[i]] = []
                if group == "Vainglory":
                    nicknames = _nick.findall(texts[i])
                    for nick in nicknames:
                        if nick not in user[domains[i]] and nick.lower() not in ignore_words and not nick.isnumeric():
                            user[domains[i]] += [nick]
                else:
                    line = texts[i].split('\n')
                    if len(line) <= 1:
                        continue
                    line = line[1]
                    if line[:3] in ["2. ", "2) "]:
                        line = line[3:]
                    if not line:
                        continue
                    user[domains[i]] = [line]   # WayLander
            # if offset % 100 == 0: print(str(offset))
        app().set(_id, len(user))
    return user     # Не обращаем внимание на пустые user[key]. Они потом обрабатываются
