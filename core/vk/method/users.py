# 01.02.2019
# секция users
from core.instance import *


def get(user_ids, fields="", name_case="nom"):
    return app().vk.call("users.get", {"user_ids": user_ids, "fields": fields, "name_case": name_case})
