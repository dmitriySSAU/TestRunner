import os
import shutil
import logging
import datetime
import threading
import configparser
from typing import List
from termcolor import colored

from scripts.common import tools

# установка формата строки лога
formatter = logging.Formatter('%(asctime)s - func %(funcName)s() - keyline=%(lineno)d - %(levelname)s - %(message)s')

# начало пути до Runner
path = ""

# режим вывода сообщений в консоль
# уровни от самого краткого до самого подробного: ERROR -> WARNING -> TEST -> ALL
# ERROR - ошибки
# WARNING - предупреждения
# TEST - различные информативные сообщения, связанные непосредственно с тестами
# ALL - любая другая различная информация
output_mode = "TEST"

# уровень логов
log_level = "INFO"

# блокировщик для функций вывода в консоль
# так как может быть несколько одновременных тестов (из разных потоков)
threadLock = threading.Lock()


def init_log() -> None:
    """Инициализация системы логирования.

       Определяется уровень вывода в консоль.
       Определяется уровень логов.
       Удалется старая директория в случае превышения лимита.
       Переименовывается папка log.
       Создается новая папка log с необходимыми подпапками.

    """
    config = configparser.ConfigParser()
    config.read("runner.conf")
    global output_mode
    output_mode = config.get("log", "output_mode")

    config = configparser.ConfigParser()
    config.read(path + "\\runner.conf")
    global log_level
    log_level = config.get("log", "level")

    delete_directory()

    rename_directory()

    os.mkdir(path + "\\log")
    os.mkdir(path + "\\log\\test")
    os.mkdir(path + "\\log\\scripts")
    os.mkdir(path + "\\log\\scripts\\ws")
    os.mkdir(path + "\\log\\scripts\\web")
    os.mkdir(path + "\\log\\scripts\\common")
    os.mkdir(path + "\\log\\scripts\\xml")
    os.mkdir(path + "\\log\\client")
    os.mkdir(path + "\\log\\log_and_statistic")


def get_logger(py_module_name: str) -> logging.Logger:
    """Получение объекта лога для указанного py-модуля

    :param py_module_name: имя py-модуля
    :return: объект лога
    """
    logger = logging.getLogger(py_module_name)
    if create_directory(py_module_name) is False:
        return logger
    fh = logging.FileHandler(path + "\\log\\" + py_module_name + "\\log.txt")
    fh.setFormatter(formatter)
    set_log_level(logger)
    logger.addHandler(fh)

    return logger


def delete_directory() -> bool:
    """Удаление самой старой директории с логами, если превышен их лимит.

    :return: либо True (если успешно удалена), либо False (если лимит не превышен)
    """
    dirs: List[str] = tools.get_dirs(path)
    log_dirs: List[str] = []

    for dir_ in dirs:
        if dir_.find("log_") != -1:
            log_dirs.append(dir_)

    config = configparser.ConfigParser()
    config.read(path + "\\runner.conf")
    max_dir = config.get("log", "max_dir")

    if len(log_dirs) < int(max_dir):
        return False

    # сортируем по возрастанию
    # самая первая - самая старая
    log_dirs.sort()
    # удаляем рекурсивно самую первую директорию
    shutil.rmtree(log_dirs[0])

    return True


def set_log_level(logger: logging.Logger) -> None:
    """Установить заданный уровень логов.

    Считывает настройку уровня из конфиг файла.

    :param logger: объект лога
    :return:
    """

    if log_level == "DEBUG":
        logger.setLevel(logging.DEBUG)

    if log_level == "INFO":
        logger.setLevel(logging.INFO)

    if log_level == "ERROR":
        logger.setLevel(logging.ERROR)

    if log_level == "CRITICAL":
        logger.setLevel(logging.CRITICAL)


def create_directory(name: str) -> bool:
    """Создание директории логов для конкретного py-модцл\

    :param name: имя py-модуля
    :return: либо True (если успешно создана), либо False
    """
    try:
        os.mkdir(path + "\\log\\" + name)
        return True
    except OSError:
        return False


def rename_directory() -> None:
    """Переименовывает папку log в папку вида log_CURRENT-TIME.

    :return: None
    """
    current_time = datetime.datetime.now()
    try:
        os.rename(path + "\\log", path + "\\log_" + current_time.strftime("%Y%m%d_%H%M%S"))
    except OSError:
        return None


def print_test(message: str) -> None:
    """Вывод в консоль сообщения уровня TEST.

    Вывод имеет зеленый цвет.
    :param message: текст сообщения для вывода
    """
    threadLock.acquire()
    if output_mode == "TEST" or output_mode == "ALL":
        print(colored(message, "green"))
    threadLock.release()


def print_warn(message: str) -> None:
    """Вывод в консоль сообщения уровня WARNING.

    Вывод имеет желтый цвет.
    :param message: текст сообщения для вывода
    """
    threadLock.acquire()
    if output_mode == "WARNING" or output_mode == "TEST" or output_mode == "ALL":
        print(colored(message, "yellow"))
    threadLock.release()


def print_error(message: str) -> None:
    """Вывод в консоль сообщения уровня ERROR.

    Вывод имеет красного цвет.
    :param message: текст сообщения для вывода
    """
    threadLock.acquire()
    print(colored(message, "red"))
    threadLock.release()


def print_all(message: str) -> None:
    """Вывод в консоль сообщения уровня ALL.

    Вывод имеет стандартный цвет (белый).
    :param message: текст сообщения для вывода
    """
    threadLock.acquire()
    if output_mode == "ALL":
        print(message)
    threadLock.release()


def raise_error(message: str, logger: logging.Logger) -> None:
    """Выброс намеренного исключения.

    Как правило, используется для завершения теста в случае ошибки
    с указанием краткого сообщения об этой ошибки.

    :param message:
    :param logger:
    """
    logger.error(message)
    raise AssertionError(message)
