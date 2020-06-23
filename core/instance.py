# 08.02.2019
# Храним тут экземпляр приложения


_app = None


def app():
    return _app


def _init():
    global _app
    import core.application
    _app = core.application.Application()


_init()
