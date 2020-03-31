import os
import colorama
from typing import List

from lib.log_and_statistic import log
from lib.log_and_statistic.statistics import Statistic

from scripts.common import tools


def init_settings():
    """Инициализация общих настроек Runner

       Определяется путь к Runner.
       Определяется уровень логов (считывается из конфиг файла).
    """
    colorama.init()

    log.path = "."


def init_run_tests() -> List[str]:
    """Получение списка тестов из тест-кейса

    Временно тест-кейс - это файл run_list.ini

    :return: список тестов вида ИМЯ-КЛАССА.ИМЯ-ТЕСТА
    """
    if not os.path.exists(log.path + '\\run_list.ini'):
        raise AssertionError("[ERROR] run_list doesn't exist!")

    run_list = []
    with open(log.path + '\\run_list.ini', encoding="utf-8") as run_list_file:
        for line in run_list_file:
            run_list.append(line.replace("\n", ""))

    return run_list


def init_data(common_input_data: dict, test_name: str, statistic: Statistic) -> dict:
    """Получение данных для нужного теста из общего json с входными данными для всех тестов.

    :param common_input_data: словарь со всеми тестами и их входными данными
    :param test_name: имя теста, для которого нужно извлечь его входные данные
    :param statistic: обхект класса Statistic
    :return: словарь с входными данными для указанного теста
    """
    logger = log.get_logger("scripts/common/initializer")
    logger.info("was called (common_input_data, test_name)")
    logger.debug("with params (" + str(common_input_data) + ", " + test_name + ")")

    test_data = {}

    for test in common_input_data['tests']:
        tools.check_keys_exist(test, ['name', 'input_data'], 'test', True, statistic)

        if test['name'] != test_name:
            continue

        test_data = test['input_data']
        logger.info("put data into 'test_data'")
        logger.debug("test_data: " + str(test_data))
        break

    if not test_data:
        statistic.append_error("empty input_data for " + test_name, "CRITICAL", True)

    return test_data
