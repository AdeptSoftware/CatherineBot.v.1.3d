# 28.02.2019
import random
from core import instance
import core.strings
import core.utils.fnstr
import core.request.vk_loader


# нужно сделать чтобы было просто обращаться к содержимому ивента
# нужно сделать чтобы легко сохранялось отовсюду и обновлялось
# не требовало бы сложных действий

def cats_n_rats(event):
    data = instance.app().disk.get("event", "cats_n_rats")
    if data is not None:
        # отправим картинку
        pid = event.get("peer_id")
        if pid is not None:
            instance.app().vk.send(pid, "", [data[3] + core.utils.fnstr.zeros(data[4] + data[0], 3)])
        else:
            instance.app().log("Event \"" + str(event.__name__) + "\" не содержит peer_id!")
        # обновим время, при котором должно будет произойти следующее событие
        event.set_next_time(random.randint(data[1], data[2])*60)
        if data[0] >= 270:
            data[0] = 1
        else:
            data[0] += 1
        instance.app().update_disk()
    else:
        instance.app().log("Для Event \"" + str(event.__name__) + "\" не имеет дефолтных данных!", use_print=True)
    return True


# загрузка ников из разрешенных обсуждений
def update_data(e):
    if e.get("flag", False) and e.set("flag", False):
        topics = e.get("topics", {})
        for key in topics:
            users = core.request.vk_loader.get_nicknames(topics[key], key, core.strings.nick_ex(), e.get("all", 1))
            e.set("all", False)
            instance.app().disk.load_nicknames(users, key)
        # обновим время
        instance.app().update_disk()
    e.set_next_time(instance.app().disk.get("event", "data_update", 900))
    return True

