# 02.05.2019


# https://oauth.yandex.ru/authorize?response_type=token&client_id=
def get():
    return {"token": "AQAAAAAX1dCLAAWlZS1xAdq510cgtYGmBejyLWs",
            "name": "Catherine"}


def version():
    return "1.3"


def get_default_storage_data(_time):
    return {"last_update": _time,                     # время последнего обновления
            "version": version(),                     # версия приложения
            "users": {},                              # пользователи и инфа о них
            "stats": {},
            "option": {                               # настройки приложения
                "app": {
                    "admin_id": 481403141,            # id admin'a (нужен перезапуск)
                    "timezone": 3},                   # временная зона
                "updates": {
                    "vk": 0.5,                        # время обновления vk, sec (нужен перезапуске)
                    "disk": 60*60,                    # обновлять диск каждые N sec
                    "request": 0.5,                   # время обновления потока с vainglory, sec (нужен перезапуск)
                    "user_profile": 12*60*60},        # обновлять пользователей каждые N sec
                "stats": {
                    "threshold_low_activity": 2,      # < N msg per min - считается низкой активностью
                    "time_interval": 30,              # время, за которое происходит сбор данных, min
                    "msg_count": ["н/д"] * 24,        # данные активности за 24ч
                    "last_msg_count": 0},             # кол-во сообщений за self._stats_time
                "event": {
                    "data_update": 1800,              # обновлять данные каждые 30 минут
                    "cats_n_rats": [1, 360, 1080, "photo-177323563_456239", 63]}}}  # "Кошки-Мышки"
