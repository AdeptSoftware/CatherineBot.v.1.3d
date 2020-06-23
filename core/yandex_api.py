import yadisk
import json
import io


class Wrapper:
    def __init__(self):
        self.api = None

    def create(self, token):
        self.api = yadisk.YaDisk(token=token)
        if not self.api.check_token():
            print("Токен для Яндекс Диска не прошёл проверку!")
            return False
        return True

    # загрузка на диск (Пример path: "CatherineBot/storage.txt")
    def upload(self, path, obj, is_string=True):
        if not is_string:
            obj = json.dumps(obj)
        bytes_io = io.BytesIO(obj.encode())
        self.api.upload(bytes_io, path, overwrite=True)
        bytes_io.close()

    # скачать с диска (Пример path: "CatherineBot/Catherine.ini")
    def download(self, path, as_string=True):
        if self.api.exists(path):
            bytes_io = io.BytesIO(b"")
            self.api.download(path, bytes_io)
            string = bytes_io.getvalue().decode('utf-8', 'backslashreplace')
            bytes_io.close()
            if not as_string:
                return json.loads(string)
            return string
        if not as_string:
            return None
        return ""

    def exists(self, path):
        return self.api.exists(path)

    def mkdir(self, path):
        return self.api.mkdir(path)
