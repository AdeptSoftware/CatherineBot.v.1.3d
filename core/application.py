# 19.01.2019
import datetime
import threading
import core.utils.convert
import core.vk.wrapper
import core.event.eventer
import core.vk.template_dialog
import core.yadisk_storage
import core.vainglory.vg_manager

from vk_api.bot_longpoll import VkBotEventType


# ======== ========= ========= ========= ========= ========= ========= =========
class Application:
    def __init__(self):
        self._debug = False
        self._dialogs = {}              # запущенные диалоги
        self._ref_names = []            # имена аккаунта
        self._storage = {}              # не сохраняются при завершении программы, но необходимы для работы
        self._disk = None               # доступ к яндекс диску
        self.disk = None                # доступ к сохранкам на яндекс диске
        self.vk = None                  # доступ к аккаунту vk
        # self.vg = None                  # менеджер запросов к Vainglory API
        self.eventer = None             # менеджер событий

    # Создание и инициализация данных
    def create(self, root_directory, token, is_debug=False, ignore_data_update=False):
        if is_debug:
            print("Инициализация...")
        # Вернет True, если все создано успешно
        self.eventer = core.event.eventer.Manager()
        self._disk = core.yadisk_storage.StorageManager()
        self.disk = core.yadisk_storage.DataStorage(self._disk.data())
        # self.vg = core.vainglory.vg_manager.Manager()
        self.vk = core.vk.wrapper.Wrapper()
        self._debug = is_debug

        # Инициализация яндекс диска и вк
        try:
            if not self._disk.create(token, root_directory):
                return False
            auth = self._disk.get_auth()
            if auth is None:
                return False
            if not self.vk.create(auth["token"], auth["id"]):
                return False
        except Exception as err:
            return self.log(str(err))
        # инициализируем диалоги:
        if is_debug:
            self.set_dialog_listener("debug", {"id": 2000000001, "group": None, "cmd": None, "handler": '$',
                                               "in_out": True})
        else:
            for name in auth["dialogs"]:
                self.set_dialog_listener(name, auth["dialogs"][name])
        # инициализируем события
        self._initialize_events(auth["topics"])
        self.eventer.start()
        # запускаем обновление ников
        if not ignore_data_update:
            self._disk.update_disk(True, True)
            self._disk.refresh_userdata()
            self.eventer.forcibly_update("data_updater", {"flag": True})
        # Выведем информацию по поводу запуска
        # self.vg.start()
        self.vk.start()
        self.log("Бот активирован", use_print=True)
        return True

    # дебаг или не дебаг
    def debug(self):
        return self._debug

    # получить параметр из хранилища
    def get(self, param, default=None):
        if param in self._storage:
            return self._storage[param]
        return default

    # записать параметр в хранилище
    def set(self, param, value):
        print("Update storage: " + str(param) + " = " + str(value))
        self._storage[param] = value

    # Создание нового прослушиваемого диалога
    def set_dialog_listener(self, name, setting):
        if setting["handler"] == '$':
            setting["handler"] = ["rs", "fast"]
        if setting["handler"]:
            i = 0
            for key in setting["handler"]:
                if key == "rs":
                    from core.rank_system.rs import main
                    setting["handler"][i] = main
                elif key == "fast":
                    from core.cmd.fast_command import analyze
                    setting["handler"][i] = analyze
                i += 1
        dlg = core.vk.template_dialog.Dialog(name, setting)
        if dlg.start():
            self._dialogs[setting["id"]] = dlg

    # Запись лога (в личку vk - себе)
    def console(self, text, obj=None):
        if obj is not None:
            text += '\n' + core.utils.convert.obj2str(obj)
        self.vk.console(text)

    # Запись лога (на Яндекс-диск)
    def log(self, text, obj=None, use_print=True, _time=True):
        if obj is not None:
            text += '\n' + core.utils.convert.obj2str(obj)
        if _time:
            text = "["+str(self.time())+"]: "+text
        if not self._debug:
            if use_print:
                print(text)
            try:
                self._disk.log(threading.currentThread().name, text)
            except Exception as err1:
                try:
                    text += "\n _disk: " + str(err1)
                    self.vk.console(text, True)
                except Exception as err2:
                    print(text + "\n vk: " + str(err2))
        else:
            print(text)
        return False

    # Получить текущее время
    def time(self):
        h = self.disk.get("app", "timezone")
        if h is None:
            return datetime.datetime.now() + datetime.timedelta(days=-40*365)
        return datetime.datetime.now() + datetime.timedelta(hours=h)

    # Завершение работы
    def exit(self, cause, safe=False):
        self.log("Завершена работа по причине: "+cause, _time=not safe)
        for name in self._dialogs:
            self._dialogs[name].stop()
        self.eventer.stop()
        self.vk.stop()
        try:
            if not self._debug:
                self._disk.update_disk(True)
        finally:
            exit(0)

    # основной цикл сообщений
    def run(self):
        admin_id = self.disk.get("app", "admin_id")
        lp = self.vk.get_long_poll()
        count, last_err = 0, None
        while True:
            try:
                for e in lp.listen():
                    if e.type == VkBotEventType.MESSAGE_NEW:
                        if e.obj["peer_id"] in self._dialogs:
                            self._dialogs[e.obj["peer_id"]].add(e.obj)
                        elif e.obj["peer_id"] == admin_id:
                            self._admin_console(e.obj)
            except Exception as err:
                if not last_err or last_err != str(err.args[0]):
                    self.log("%s (x%d)" % (err, count))
                    last_err = str(err.args[0])
                    count = 1
                else:
                    count += 1

    # обновить данные
    def update_disk(self):
        self._disk.update_disk(True)

    # последняя команда
    def get_last_cmd_info(self, peer_id, user_id, ignore_common_cmd=False):
        if peer_id in self._dialogs:
            return self._dialogs[peer_id].get_last_cmd_info(user_id, ignore_common_cmd)
        return None

    # ==== ========= ========= ========= ========= ========= ========= =========
    # Методы, которые нельзя вызывать

    # Инициализация событий
    def _initialize_events(self, topics):
        import core.event.handlers.fn_update as _u
        self.eventer.new(core.event.eventer.Event("data_updater", _u.update_data, {"flag": False,
                                                                                   "all": False,
                                                                                   "topics": topics}))

    # вызывается редко и только админом
    def _admin_console(self, item):
        try:
            if "!refresh" in item["text"]:
                text = "обновление"
                if "userdata" in item["text"]:
                    text += " userdata"
                    self._disk.refresh_userdata()
                elif "nick" in item["text"]:
                    flag = False
                    text += " списка ников"
                    if "all" in item["text"]:
                        text += " (расширенное)"
                        flag = True
                    self.eventer.forcibly_update("data_updater", {"flag": True, "all": flag})
                self.vk.console("Успешно завершено! " + text)
            if item["text"][:9] == "!set rank":
                import core.cmd.fast_command
                self.vk.console(core.cmd.fast_command.update_ranks(item["text"]))
            if item["text"] == "!save":
                self._disk.update_disk(True)
        except Exception as err:
            self.log(str(err))
