from lib.log_and_statistic import log
from lib.runner import initializer
from lib.runner.runner import Runner

from gui import run as qml


def main():
    """Функция запуски различной инициализации настроек и тест кейсов.

    """
    initializer.init_settings()
    log.init_log()

    runner = Runner()
    runner.start()


if __name__ == "__main__":
    #qml.run()
    main()
