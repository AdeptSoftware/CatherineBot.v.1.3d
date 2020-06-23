# 07.02.2019


# Проверка ника
def is_nickname(text):
    if text is None:
        return -1
    length = len(text)
    if length < 3 or length > 16:
        return -1
    for c in text:
        if not (('A' <= c <= 'Z') or ('a' <= c <= 'z') or ('0' <= c <= '9') or c == '_'):
            return 0
    return 1


# вернет число больше 0 если это ссылка вк
def is_vk_ref(words, i, length):
    skip_count = 0
    if words[i][1] in ["http", "https"]:
        if words[i][2] != "://":
            return -1           # таких ников не существует по данным сайтов
        skip_count += 1
    if i+skip_count < length and words[i+skip_count][1] == "vk":
        if words[i+skip_count][2] != '.':
            return -1           # слишком короткий для ника
        skip_count += 1
    else:
        if skip_count != 0:
            return -1   # по позиции i стоят http и https - что не может быть ником или domain'om
    if i+skip_count < length and words[i+skip_count][1] == "com":
        if words[i+skip_count][2] != '/' or skip_count == 0:
            return -1
        skip_count += 1
    else:
        if skip_count != 0:
            return -1
    return skip_count