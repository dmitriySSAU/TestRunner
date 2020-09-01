import os
import shutil
import datetime
import logging
import logging.handlers
from typing import List

from scripts.common import tools


class Log:
    def __init__(self, config: dict):
        print("create_log")
        # установка формата строки лога
        self._formatter = logging.Formatter('%(asctime)s - func %(funcName)s() - keyline=%(lineno)d - '
                                            '%(levelname)s - %(message)s')
        self._log_level = config['log']['level']
        self._max_bytes = config['log']['max_bytes']
        self._max_files = config['log']['max_files']

        delete_directory(config['log']['max_dir'])
        rename_directory()
        create_root_directories()

    def get_logger(self, py_module_name: str) -> logging.Logger:
        """Получение объекта лога для указанного py-модуля

        :param py_module_name: имя py-модуля.

        :return: объект лога.
        """
        logger = logging.getLogger(py_module_name)
        if logger.handlers:
            return logger
        if create_directory(py_module_name) is False:
            return logger
        fh = logging.handlers.RotatingFileHandler("./log/" + py_module_name + "/log.txt", maxBytes=self._max_bytes,
                                                  backupCount=self._max_files)
        fh.setFormatter(self._formatter)
        self._set_log_level(logger)
        logger.addHandler(fh)

        return logger

    def _set_log_level(self, logger: logging.Logger) -> None:
        """Установить заданный уровень логов.

        Считывает настройку уровня из конфиг файла.

        :param logger: объект лога.
        """
        if self._log_level == "DEBUG":
            logger.setLevel(logging.DEBUG)

        if self._log_level == "INFO":
            logger.setLevel(logging.INFO)

        if self._log_level == "ERROR":
            logger.setLevel(logging.ERROR)

        if self._log_level == "CRITICAL":
            logger.setLevel(logging.CRITICAL)


def delete_directory(max_dir: int) -> bool:
    """Удаление самой старой директории с логами, если превышен их лимит.

    :return: либо True (если успешно удалена), либо False (если лимит не превышен)
    """
    print("delete_directory")
    dirs: List[str] = tools.get_dirs("./")
    log_dirs: List[str] = []

    for dir_ in dirs:
        if dir_.find("log_") != -1:
            log_dirs.append(dir_)

    if len(log_dirs) < max_dir:
        return False

    # сортируем по возрастанию
    # самая первая - самая старая
    log_dirs.sort()
    # удаляем рекурсивно самую первую директорию
    shutil.rmtree(log_dirs[0])

    return True


def create_root_directories():
    os.mkdir("./log")
    os.mkdir("./log/test")
    os.mkdir("./log/scripts")
    os.mkdir("./log/scripts/ws")
    os.mkdir("./log/scripts/web")
    os.mkdir("./log/scripts/common")
    os.mkdir("./log/scripts/xml")
    os.mkdir("./log/client")
    os.mkdir("./log/log_and_statistic")


def create_directory(name: str) -> bool:
    print("create_directory")
    """Создание директории логов для конкретного py-модуля.

    :param name: имя py-модуля
    :return: либо True (если успешно создана), либо False
    """
    if os.path.exists("./log/" + name):
        return True
    try:
        os.mkdir("./log/" + name)
        return True
    except OSError:
        return False


def rename_directory() -> None:
    """Переименовывает папку log в папку вида log_CURRENT-TIME.

    :return: None
    """
    if os.path.exists("./log"):
        current_time = datetime.datetime.now()
        os.renames("./log", "./log_" + current_time.strftime("%Y%m%d_%H%M%S"))


def raise_error(message: str, logger: logging.Logger) -> None:
    """Выброс намеренного исключения.

    Как правило, используется для завершения теста в случае ошибки
    с указанием краткого сообщения об этой ошибки.

    :param message:
    :param logger:
    """
    logger.error(message)
    raise AssertionError(message)
