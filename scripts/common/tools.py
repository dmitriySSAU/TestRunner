import os
import json
import base64
import subprocess
from typing import List
from datetime import datetime
from datetime import timedelta

from lib.log_and_statistic import log
from lib.client.soapClient import SoapClient
from lib.log_and_statistic.statistics import Statistic

from scripts.common import db
from scripts.ws import ipcameras


def get_dirs(path: str) -> List[str]:
    """Возвращает список директорий по указанному пути.

    :param path: путь к директориям
    :return: список директорий
    """
    for root in os.walk(path + "\\"):
        dirs = root[1]
        return dirs


def get_files(path: str) -> List[str]:
    """Возвращает список файлов по указанному пути.

    :param path: путь к директориям
    :return: список файлов
    """
    for root in os.walk(path + "\\"):
        files = root[2]
        return files


def check_keys_exist(dict_on_check: dict, keys: list, dict_name: str, is_critical: bool, statistic: Statistic) -> bool:
    """
    проверка на наличия ключей в словаре

    :param dict_on_check: словарь к проверке
    :param keys: список ключей, на существование которых идет проверка
    :param dict_name: имя проверяемого словаря для понимания пользователем
    :param is_critical: флаг - выбрасывать исключение при отсутствии ключа или нет и отпечатать только сообщение
    :param statistic: экземляр класса Statistic для добавления ошибок и предупреждений
    """
    logger = log.get_logger("scripts/common/tools")
    logger.info("was called")
    logger.debug("with params (" + str(dict_on_check) + ", " + str(keys) + ", " + dict_name + ", " +
                 str(is_critical) + ")")

    if isinstance(dict_on_check, dict) is False:
        statistic.append_error("'" + dict_name + "'", "НЕТ_СЛОВАРЯ", True)

    success = True
    for key in keys:
        if key not in dict_on_check:
            success = False
            if is_critical:
                statistic.append_error("'" + key + "' в '" + dict_name + "'!", "НЕТ_КЛЮЧА", True)
            else:
                logger.error("'" + key + "' в '" + dict_name + "'!")
                statistic.append_error("'" + key + "' в '" + dict_name + "'!", "НЕТ_КЛЮЧА", False)

    return success


def open_json_file(path: str, statistic: Statistic) -> dict:
    """Открытие файла с содержимым в формате json.

    Функция считывает json из файла и преобразует в словарь.
    Если файл не существует - генерируется критическая ошибка
    :param path: путь к файлу
    :param statistic: объект класса Statistic
    :return: сожержимое json файла в виде словаря
    """
    logger = log.get_logger("scripts/common/tools")
    logger.info("was called (path: str, statistic: Statistic)")
    logger.debug("with params (" + path + ", statistic_obj)")

    if not os.path.exists(path):
        statistic.append_error(path, "НЕ_СУЩЕСТВУЕТ", True)

    with open(path, encoding='utf-8') as json_file:
        try:
            logger.info("open json file '" + path + "' was executed successfully")
            log.print_all("Открытие файла '" + path + "' выполнено успешно...")
            return json.load(json_file)
        except json.JSONDecodeError:
            logger.error("В файле '" + path + "' отсутствует корректная строка JSON!")
            statistic.append_error("В файле '" + path + "' отсутствует корректная строка JSON!", "НЕВАЛИД_ЗНАЧ", True)


def write_to_file(path: str, content: str) -> None:
    """Функция записи в файл.

    :param path: путь к файлу
    :param content: содержимое для записи
    """
    logger = log.get_logger("scripts/common/tools")
    logger.info("was called (path: str, content: str)")
    logger.debug("with params (" + path + ", " + content + ")")
    with open(path, 'w') as txt_file:
        txt_file.write(content)
        logger.info("write content to file '" + path + "' was executed successfully!")
        log.print_all("Запись в файл '" + path + "' выполнена успешно!")


def get_list_with_filter(list_: list, filter_: str) -> list:
    """Фильтрация значений из списка.

    Функция поддерживает фильтры со звездочками (*)

    :param list_: список значений для фильтрации
    :param filter_: фильтр
    :return: список с отфильтрованными значениями
    """
    list_with_filter = []

    is_asterisk_exist = True
    if filter_.find("*") == -1:
        is_asterisk_exist = False
    # если фильтр звездочка, то возвращаем целиком весь список
    if len(filter_) == 1 and is_asterisk_exist:
        return list_

    # если звездочка (фильтр) есть, то
    # находим строку до звездочки
    # и после
    if is_asterisk_exist:
        # до
        str_begin = filter_[0:filter_.find("*")]
        str_end = ""
        # после
        if filter_.find("*") + 1 < len(filter_):
            str_end = filter_[filter_.find("*") + 1:]

    for element in list_:
        if is_asterisk_exist:
            if element.startswith(str_begin) is False:
                continue
            if element.endswith(str_end) is False:
                continue
        else:
            if element != filter_:
                continue
        list_with_filter.append(element)

    return list_with_filter


def get_full_dict(dicts: list) -> dict:
    """Получения словаря путем склейки словарей из списка.

    Используется для преобразования словарей профилей графа в один целый словарь.
    :param dicts: список словарей
    :return: полный словарь после склейки
    """
    dicts_items: list = []
    for dict_ in dicts:
        dicts_items += dict_.items()

    return dict(dicts_items)


def get_file_type(file: str) -> str:
    """Функция извлечения типа файла.

    :param file: имя файла
    :return: тип файла
    """
    point_index = file.find(".")
    if point_index < 0:
        return ""
    return file[point_index:]


def get_dump_name_and_step(path_to_dump: str) -> tuple:
    """Получение имени дампа камеры и номера шага

    :param: path_to_dump: путь до файла дампа
    :return: кортеж: 0 - имя дамп фафйла, 1 - номер шага
    """
    index_num_step_begin = path_to_dump.index("Step") + 4
    dump_name = ""
    step_number = ""
    index = 0
    while index < index_num_step_begin - 4:
        dump_name += path_to_dump[index]
        index += 1
    while path_to_dump[index_num_step_begin] != '.':
        step_number += path_to_dump[index_num_step_begin]
        index_num_step_begin += 1

    return dump_name, int(step_number)


def get_statistic_by_cam(client: SoapClient, key1: str, key2: str, statistic: Statistic) -> dict:
    """Получение статистики по указанной камере.

    Использует ws метод list_statistic_for_profiles

    :param client: объект клиента класса SoapClient
    :param key1: key1 IV7 (имя сервреа)
    :param key2: key2 IV7 (имя камеры)
    :param statistic: объект класса Statistic
    :return: ответ ws метода - статистика по указанной камере
    """
    logger = log.get_logger("scripts/common/tools")
    logger.info("was called (client: SoapClient, key1: str, key2: str)")
    logger.debug("with params (client_obj, " + key1 + ", " + key2 + ")")

    logger.info("call func ipcameras.list_statistic_for_profiles(client, token)")
    logger.debug("ipcameras.list_statistic_for_profiles(client_obj, '')")
    all_stat = ipcameras.list_statistic_for_profiles(client, "")

    if not all_stat:
        return {}

    for stat in all_stat:
        check_keys_exist(stat, ['key1', 'key2'], 'statistic_for_profiles', True, statistic)
        if stat['key2'] == key2 and stat['key1'] == key1:
            return stat
    return {}


def get_max_value_by_key(dicts: list, key: str, statistic: Statistic) -> int:
    """Поиск максимума в списке словарей по ключу.

    :param dicts: список словарей
    :param key: имя ключа
    :param statistic: объект класса Statistic
    :return: максимальное найденное значение
    """
    max_val = 0
    for dict_ in dicts:
        if key not in dict_:
            statistic.append_warn(key, "НЕТ_КЛЮЧА")
        if dict_[key] > max_val:
            max_val = dict_[key]
    return max_val


def get_date_from_str(current_date: str) -> datetime:
    """Функция возвращает datetime из строки

    Аргумент current_date может быть вида:
        1) %Y.%m.%d %H:%M:%S
        2) %Y-%m-%dT%H:%M-%S
        3) %Y-%m-%d %H:%M:%S
    :param current_date: строка текущей даты
    :return: datetime
    """
    if current_date.find(".") > -1:
        return datetime.strptime(current_date, '%Y.%m.%d %H:%M:%S')
    if current_date.find("T") > -1:
        return datetime.strptime(current_date, '%Y-%m-%dT%H:%M-%S')

    return datetime.strptime(current_date, '%Y-%m-%d %H:%M:%S')


def increment_time(time: datetime, increment: int) -> datetime:
    """Увеличивает время datetime на инкремент в секундах.

    :param time: объект времени datetime
    :param increment: время-инкремент в секундах
    :return:
    """
    return time + timedelta(seconds=increment)


def convert_time_to_gtc(time: datetime) -> datetime:
    """Преобразование текущего времени в GTC (-4)

    :param time:
    :return: объект времени datetime с разницей в 4 часа
    """
    return time - timedelta(hours=4)


def get_dict_by_keys_values(dicts: list, keys: list, values: list) -> int:
    """Функция получения индекса словаря в массиве по значиняем указанных ключей.

    :param dicts: список словарей
    :param keys: список ключей
    :param values: список значений для ключей соответственно
    :return: либо индекс словаря в массиве, либо -1, если такой не будет найдет
    """
    dict_result_index: int = -1
    for dict_index, dict_ in enumerate(dicts):
        for key_index, key in enumerate(keys):
            if key not in dict_:
                break
            if dict_[key] != values[key_index]:
                break
            if key_index == len(keys) - 1:
                return dict_index
    return dict_result_index


def cmd_exec(cmd: str, find: str) -> bool:
    """Выполнение команды в терминале и поиск указанного вхождения в результате команды.

    :param cmd: команда
    :param find: вхождение, которое нужно будет искать в результате
    :return: флаг обнаружения вхождения в результате выполнения команды
    """
    cmd_result_get_search_proc = str(subprocess.check_output(cmd, shell=True))
    if cmd_result_get_search_proc.find(find) == -1:
        return False
    return True


def get_photos_base64(photo_paths: List[str]) -> List[str]:
    """Преобразование картинок в base64

    :param photo_paths: путь к картинке
    :return: строка в формате base64
    """
    photos_base64: list = []
    for photo in photo_paths:
        with open(photo, "rb") as image_file:
            base64_photo = base64.b64encode(image_file.read())
            str_base64_photo = base64_photo.decode("utf-8")
            photos_base64.append(str_base64_photo)
    return photos_base64


def check_types(names: List[str], values: list, types: list, statistic: Statistic) -> None:
    """Проверка типов значений

    :param names: список имен значений
    :param values: список значений
    :param types: список типов
    :param statistic: объект класса Statistic
    """
    for index, value in enumerate(values):
        if isinstance(value, types[index]) is False:
            statistic.append_error("'" + str(value) + "' ключ '" + names[index] + "'... требуется " + str(types[index]),
                                   "НЕВАЛИД_ТИП", True)


def check_values(names: List[str], values: list, need_values: list, operations: List[str], statistic: Statistic) -> None:
    """Проверка на соответствие значений требованиеям

    :param names: список имен значений
    :param values: список значений
    :param need_values: список требований (нужных значений)
    :param operations: список операций для сравнения значений с требованиями
    :param statistic: объект класса Statistic
    """
    for index, value in enumerate(values):
        if operations[index] == "!=":
            if value == need_values[index]:
                statistic.append_error("'" + str(value) + "' ключ '" + names[index] + "'... требуется != "
                                       + str(need_values[index]), "НЕВАЛИД_ЗНАЧ", True)
            continue
        if operations[index] == "==":
            if value != need_values[index]:
                statistic.append_error("'" + str(value) + "' ключ '" + names[index] + "'... требуется == "
                                       + str(need_values[index]), "НЕВАЛИД_ЗНАЧ", True)
            continue
        if operations[index] == ">":
            if value <= need_values[index]:
                statistic.append_error("'" + str(value) + "' ключ '" + names[index] + "'... требуется > "
                                       + str(need_values[index]), "НЕВАЛИД_ЗНАЧ", True)
            continue
        if operations[index] == "<":
            if value >= need_values[index]:
                statistic.append_error("'" + str(value) + "' ключ '" + names[index] + "'... требуется < "
                                       + str(need_values[index]), "НЕВАЛИД_ЗНАЧ", True)
            continue
        if operations[index] == ">=":
            if value < need_values[index]:
                statistic.append_error("'" + str(value) + "' ключ '" + names[index] + "'... требуется >= "
                                       + str(need_values[index]), "НЕВАЛИД_ЗНАЧ", True)
            continue
        if operations[index] == "<=":
            if value > need_values[index]:
                statistic.append_error("'" + str(value) + "' ключ '" + names[index] + "'... требуется <= "
                                       + str(need_values[index]), "НЕВАЛИД_ЗНАЧ", True)
            continue


def get_next_cam(keys1: list, keys2: list, keys3: list, curr_key1: str, curr_key2: str, curr_key3: str,
                 statistic: Statistic) -> tuple:
    """Функия получение следующей камеры из списка на основе предыдущей.

    :param keys1: список серверов
    :param keys2: список имен камер на сервере
    :param keys3: список профилей для камер
    :param curr_key1: крайний сервер
    :param curr_key2: крайняя камера
    :param curr_key3: крайний профиль
    :param statistic: объект класса Statistic
    :return: кортеж со слеюущим именем сервера, именем камеры и профилем
    """
    logger = log.get_logger("scripts/common/graph")
    logger.info("was called (keys1: list, keys2: list, keys3: list, curr_key1: str, curr_key2: str, curr_key3: str")
    logger.debug("get_next_cam(" + str(keys1) + ", " + str(keys2) + ", " + str(keys3) + ", " + curr_key1 + ", " +
                 curr_key2 + ", " + curr_key3 + ")")

    index_curr_key1 = keys1.index(curr_key1)
    if index_curr_key1 == -1:
        statistic.append_error("Сервера '" + curr_key1 + " нет в списке!", "КРИТ", True)

    if curr_key2 == "" and curr_key3 == "":
        index_curr_key2 = 0
        index_curr_key3 = -1
    else:
        index_curr_key2 = keys2.index(curr_key2)
        if index_curr_key2 == -1:
            statistic.append_error("Камеры '" + curr_key2 + "' нет в списке!", "КРИТ", True)

        index_curr_key3 = keys3.index(curr_key3)
        if index_curr_key3 == -1:
            statistic.append_error("Профиля '" + curr_key3 + "' нет в списке!", "КРИТ", True)

    for index_key2 in range(index_curr_key2, len(keys2)):
        # перебор профилей камеры - начинаем со следующего после текущего
        for index_key3 in range(index_curr_key3 + 1, len(keys3)):
            new_key1 = keys1[index_curr_key1]
            new_key2 = keys2[index_key2]
            new_key3 = keys3[index_key3]
            return new_key1, new_key2, new_key3
        # если профилей больше нет, то выставляем индекс таким образом,
        # чтобы для следующей камеры перебор профилей началася сначала
        index_curr_key3 = -1

    # если есть еще сервера, то продвигаемся дальше
    if index_curr_key1 < len(keys1) - 1:
        return keys1[index_curr_key1 + 1], "", ""

    return ()


def get_next_cam_json(curr_key1: str, curr_key2: str, curr_key3: str, previous_key1: str, path_to_db: str,
                      _filter: dict, keys1: list, keys2: list, statistic: Statistic) -> tuple:
    """Функция получения json следующей камеры , основываясь на текущей последней взятой камеры
       из списков отфильтрованных камер для текущего сервера из списка отфильтрованных серверов.

    Первый запуск функции должен быть с параметрами:
    (имя сервера, "", "", "", путь к бд, _filter, список серверов, пустой список, статистика)

    _filter - словарь, в котором обязательно должны быть такие поля как:
    key2 и key3, где key2 - фильтр для имени камеры, а key3 - список профилей.

    :param curr_key1: имя текущего сервера
    :param curr_key2: имя текущей камеры
    :param curr_key3: имя текущего профиля
    :param previous_key1: предыдущий сервер
    :param path_to_db: путь к файлу БД
    :param _filter: словарь фильтров для камеры
    :param keys1: список серверов
    :param keys2: список камер
    :param statistic: объект класса Statistic
    :return: кортеж: 0 - json камеры, 1 - имя сервера, 2 - имя камеры, 3 - имя профиля.
    - если вернется {}, "", "", "", [] - то это признак окончания полного прохода
    - если вернется{}, имя_сервера, "", "", [] - то значит был переход на следующий сервер и список камер нужно
    получить новый
    """
    logger = log.get_logger("scripts/common/tools")
    logger.info("was called func get_next_cam(curr_key1, curr_key2, curr_key3, previous_key1, path_to_db, _filter,"
                " list_key1, list_key2")
    logger.debug("get_next_cam(" + curr_key1 + ", " + curr_key2 + ", " + curr_key3 + ", " + previous_key1
                 + ", " + path_to_db + ", " + str(_filter) + ", " + str(keys1) + ", " + str(keys2) + ")")
    # получение списка камер с сервера, а затем
    # получение списка камер, согласно выставленному фильтру в текущем элементе массива json cam
    if previous_key1 != curr_key1:
        list_key2 = get_list_with_filter(db.get_lists_key2_and_id54(path_to_db, curr_key1, statistic)[0], _filter['key2'])
        if not list_key2:
            log.print_error("Skipping filter '" + _filter['key2'] + "' on server '" + curr_key1 + "'...")
        previous_key1 = curr_key1
    # получение данных по следующей камере
    cam_data = get_next_cam(keys1, keys2, _filter['key3'], curr_key1, curr_key2, curr_key3, statistic)
    # признак завершения полного прохода по всем серверам, камерам и профилям
    if not cam_data:
        return {}, "", "", "", []
    curr_key1 = cam_data[0]
    curr_key2 = cam_data[1]
    curr_key3 = cam_data[2]
    # если сменился сервер, то нужно получить список камер для него и получить "следующую камеру"
    if previous_key1 != curr_key1:
        return {}, curr_key1, "", "", []

    # выполняем SELECT из базы - получаем json камеры и преобразуем его в словарь
    logger.info("current operation: get_dict_full_json_graph_by_cam")
    logger.info("call func db.get_dict_full_json_graph_by_cam(path_to_db, key1, key2, key3)")
    logger.debug("db.get_dict_full_json_graph_by_cam(" + path_to_db + ", " + curr_key1 + ", " + curr_key2 + ", " +
                 curr_key3 + ")")
    json_cam: dict = db.get_full_json_graph_by_cam(path_to_db, curr_key1, curr_key2, curr_key3, statistic)

    return json_cam, curr_key1, curr_key2, curr_key3, keys2
