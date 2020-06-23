# app.py
# AdeptSoftware (c) 19.01.2018

# Требования к приложению:
# 1. Развитая Debug-система
# 2. Простота
# 3. Модульность
# 4. Мультипоточность

import time
import application_data
from core.instance import *


# точка входа
def _main(is_debug=False, ignore_data_update=False):
    data = application_data.get()
    while True:
        try:
            if _create(data["name"], data["token"], is_debug, ignore_data_update):
                app().run()
            else:
                app().exit("Завершена работа приложения, т.к. не удалось переподключиться!", True)
        except Exception as err:
            app().log(str(err))


# ======== ========= ========= ========= ========= ========= ========= =========
# Создание приложения
def _create(token, directory, is_debug=False, ignore_data_update=False):
    i = 0
    while i < 5:
        if app().create(token, directory, is_debug, ignore_data_update):
            return True
        else:
            i += 1
            time.sleep(2)
    return False


# ======== ========= ========= ========= ========= ========= ========= =========
# https://oauth.yandex.ru/authorize?response_type=token&client_id=
_main()
