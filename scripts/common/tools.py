import os
import json
import base64
import subprocess
from typing import List
from typing import Tuple
from datetime import datetime, timezone
from datetime import timedelta

from lib.client.soapClient import SoapClient
from lib.log_and_statistic.statistic import Statistic

from scripts.common import db
from scripts.ws import ipcameras


def get_dirs(path: str) -> Tuple[str]:
    """Возвращает список директорий по указанному пути.

    :param path: путь к директориям.

    :return: список директорий.
    """
    for root in os.walk(path):
        dirs = root[1]
        return tuple(dirs)


def get_files(path: str) -> Tuple[str]:
    """Возвращает список файлов по указанному пути.

    :param path: путь к директориям.

    :return: список файлов.
    """
    for root in os.walk(path + "/"):
        files = root[2]
        return tuple(files)


def check_keys_exist(dict_on_check: dict, keys: list, dict_name: str, is_critical: bool, statistic: Statistic) -> bool:
    """проверка на наличия ключей в словаре.

    :param dict_on_check: словарь к проверке;
    :param keys: список ключей, на существование которых идет проверка;
    :param dict_name: имя проверяемого словаря для понимания пользователем;
    :param is_critical: флаг - выбрасывать исключение при отсутствии ключа или нет и отпечатать только сообщение;
    :param statistic: экземляр класса Statistic для добавления ошибок и предупреждений.

    :return: флак успешности проверки.
    """
    logger = statistic.get_log().get_logger("scripts/common/tools")
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
                statistic.append_error("'" + key + "' в '" + dict_name + "'!", "НЕТ_КЛЮЧА")

    return success


def open_json_file(path: str, statistic: Statistic) -> dict:
    """Открытие файла с содержимым в формате json.
    Функция считывает json из файла и преобразует в словарь.
    Если файл не существует - генерируется критическая ошибка.

    :param path: путь к файлу;
    :param statistic: объект класса Statistic.

    :return: сожержимое json файла в виде словаря.
    """
    logger = statistic.get_log().get_logger("scripts/common/tools")
    logger.info("was called (path: str, statistic: Statistic)")
    logger.debug("with params (" + path + ", statistic_obj)")

    if not os.path.exists(path):
        statistic.append_error(path, "НЕ СУЩЕСТВУЕТ", True)

    with open(path, encoding='utf-8') as json_file:
        try:
            logger.info("open json file '" + path + "' was executed successfully")
            result = json.load(json_file)
            statistic.append_info("Открытие файла '" + path + "' выполнено успешно...", "JSON_ФАЙЛ")
            return result
        except json.JSONDecodeError:
            logger.error("В файле '" + path + "' отсутствует корректная строка JSON!")
            statistic.append_error("В файле '" + path + "' отсутствует корректная строка JSON!", "JSON_ФАЙЛ", True)


def write_to_file(path: str, content: str, statistic: Statistic) -> None:
    """Функция записи в файл.

    :param path: путь к файлу;
    :param content: содержимое для записи;
    :param statistic: объект класса Statistic.
    """
    logger = statistic.get_log().get_logger("scripts/common/tools")
    logger.info("was called (path: str, content: str)")
    logger.debug("with params (" + path + ", " + content + ")")
    with open(path, 'w') as txt_file:
        txt_file.write(content)
        logger.info("write content to file '" + path + "' was executed successfully!")
        statistic.append_info("Запись в файл '" + path + "' выполнена успешно!", "ИНФО")


def get_list_with_filter(list_: tuple, filter_: str) -> Tuple[str]:
    """Фильтрация значений из списка.

    Функция поддерживает фильтры со звездочкой (*).

    :param list_: список значений для фильтрации;
    :param filter_: фильтр.

    :return: список с отфильтрованными значениями.
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
    str_middle = ""
    if is_asterisk_exist:
        if filter_.count("*") == 2:
            first_aster = filter_.find("*")
            second_aster = filter_.find("*", first_aster + 1)
            str_middle = filter_[first_aster + 1:second_aster]
        # до
        str_begin = filter_[0:filter_.find("*")]
        str_end = ""
        # после
        if filter_.find("*") + 1 < len(filter_):
            str_end = filter_[filter_.find("*") + 1:]
    for element in list_:
        if is_asterisk_exist:
            if str_middle:
                if element.find(str_middle) != -1 and element.startswith(str_middle) is False and element.startswith(str_middle) is False:
                    list_with_filter.append(element)
                    continue
            if element.startswith(str_begin) is False:
                continue
            if element.endswith(str_end) is False:
                continue
        else:
            if element != filter_:
                continue
        list_with_filter.append(element)
    return tuple(list_with_filter)


def get_full_dict(dicts: list) -> dict:
    """Получения словаря путем склейки словарей из списка.
    Используется для преобразования словарей профилей графа в один целый словарь.

    :param dicts: список словарей.

    :return: полный словарь после склейки.
    """
    dicts_items: list = []
    for dict_ in dicts:
        dicts_items += dict_.items()

    return dict(dicts_items)


def get_file_type(file: str) -> str:
    """Функция извлечения типа файла.

    :param file: имя файла.

    :return: тип файла.
    """
    point_index = file.find(".")
    if point_index < 0:
        return ""
    return file[point_index + 1:]


def get_dump_name_and_step(path_to_dump: str) -> tuple:
    """Получение имени дампа камеры и номера шага.

    :param: path_to_dump: путь до файла дампа.

    :return: кортеж: 0 - имя дамп фафйла, 1 - номер шага.
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
    Использует ws метод list_statistic_for_profiles.

    :param client: объект клиента класса SoapClient;
    :param key1: key1 IV7 (имя сервреа);
    :param key2: key2 IV7 (имя камеры);
    :param statistic: объект класса Statistic.

    :return: ответ ws метода - статистика по указанной камере.
    """
    logger = statistic.get_log().get_logger("scripts/common/tools")
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

    :param dicts: список словарей;
    :param key: имя ключа;
    :param statistic: объект класса Statistic.

    :return: максимальное найденное значение.
    """
    max_val = 0
    for dict_ in dicts:
        if key not in dict_:
            statistic.append_warn(key, "НЕТ КЛЮЧА")
        if dict_[key] > max_val:
            max_val = dict_[key]
    return max_val


def get_date_from_str(current_date: str, statistic: Statistic) -> datetime:
    """Функция возвращает datetime из строки.

    Аргумент current_date может быть вида:
        1) %Y.%m.%d %H:%M:%S
        2) %Y-%m-%dT%H:%M-%S
        3) %Y-%m-%d %H:%M:%S
        4) %Y-%m-%d %H:%M:%S.%f
    :param current_date: строка текущей даты;
    :param statistic: объект класса Statistic.

    :return: datetime.
    """
    logger = statistic.get_log().get_logger("scripts/common/tools")
    logger.info("was called (current_date: str)")
    logger.debug("params (client_obj, " + current_date + ")")

    formats = ['%Y.%m.%d %H:%M:%S', '%Y-%m-%dT%H:%M-%S', '%Y-%m-%d %H:%M:%S', "%Y-%m-%d %H:%M:%S.%f"]
    for format_ in formats:
        try:
            return datetime.strptime(current_date, format_)
        except ValueError:
            continue
    statistic.append_error("Не поддерживаемый формат даты " + current_date + "!", "НЕВАЛИД ФОРМАТ", True)


def increment_time(time: datetime, increment: int) -> datetime:
    """Увеличивает время datetime на инкремент в секундах.

    :param time: объект времени datetime;
    :param increment: время-инкремент в секундах.

    :return: объект datetime с инкрементированным временем.
    """
    return time + timedelta(seconds=increment)


def decrement_time(time: datetime, decrement: int) -> datetime:
    """Уменьшает время datetime на инкремент в секундах.

    :param time: объект времени datetime;
    :param decrement: время-декремент в секундах.

    :return: объект datetime с денкрементированным временем.
    """
    return time - timedelta(seconds=decrement)


def convert_time_to_gtc(time: datetime) -> datetime:
    """Преобразование текущего времени в GTC (-4).

    :param time: объект datetime.

    :return: объект времени datetime с разницей в 4 часа.
    """
    return time - timedelta(hours=4)


def convert_time_from_gtc(utc_time: datetime) -> datetime:
    """Конвертирование времени из utc в локальное.

    :param utc_time: объект datetime с utc временем.

    :return: объект datetime с локальным временем.
    """
    return utc_time.replace(tzinfo=timezone.utc).astimezone(tz=None)


def get_dict_by_keys_values(dicts: tuple, keys: tuple, values: tuple) -> int:
    """Функция получения индекса словаря в массиве по значиняем указанных ключей.

    :param dicts: список словарей;
    :param keys: список ключей;
    :param values: список значений для ключей соответственно.

    :return: либо индекс словаря в массиве, либо -1, если такой не будет найдет.
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

    :param cmd: команда;
    :param find: вхождение, которое нужно будет искать в результате.

    :return: флаг обнаружения вхождения в результате выполнения команды.
    """
    cmd_result_get_search_proc = str(subprocess.check_output(cmd, shell=True))
    if cmd_result_get_search_proc.find(find) == -1:
        return False
    return True


def cmd_exec(cmd: str) -> str:
    """Выполнение команды в терминале.

    :param cmd: команда
    :return: строка резултата выполнения команды
    """
    try:
        cmd_result_get_search_proc: str = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        cmd_result_get_search_proc = e.output

    return cmd_result_get_search_proc


def get_photos_base64(photo_paths: Tuple[str]) -> Tuple[str]:
    """Преобразование картинок в base64.

    :param photo_paths: кортеж с путями к картинками.

    :return: кортеж с base64.
    """
    photos_base64: list = []
    for photo in photo_paths:
        with open(photo, "rb") as image_file:
            base64_photo = base64.b64encode(image_file.read())
            str_base64_photo = base64_photo.decode("utf-8")
            photos_base64.append(str_base64_photo)
    return tuple(photos_base64)


def check_types(names: List[str], values: list, types: list, statistic: Statistic) -> None:
    """Проверка типов значений.

    :param names: список имен значений;
    :param values: список значений;
    :param types: список типов;
    :param statistic: объект класса Statistic.
    """
    for index, value in enumerate(values):
        # студия подчеркивает красным, но этом работает...
        if isinstance(value, types[index]) is False:
            statistic.append_error("'" + str(value) + "' ключ '" + names[index] + "'... требуется " + str(types[index]),
                                   "НЕВАЛИД_ТИП", True)


def check_values(names: List[str], values: list, need_values: list, operations: List[str], statistic: Statistic) -> None:
    """Проверка на соответствие значений требованиеям.

    :param names: список имен значений;
    :param values: список значений;
    :param need_values: список требований (нужных значений);
    :param operations: список операций для сравнения значений с требованиями;
    :param statistic: объект класса Statistic.
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


def get_next_cam(cams: tuple, profiles: tuple, previous_cam: str = "", previous_profile: str = "") -> tuple:
    """Функия получение следующей камеры из списка на основе предыдущей.

    :param cams: список имен камер на сервере;
    :param profiles: список профилей для камер;
    :param previous_cam: предыдущая камера;
    :param previous_profile: предыдущий профиль.

    :return: кортеж со слеюущим именем камеры и профилем. Если были перебраны все камеры по всем профилям, то
    вернется пустой кортеж.
    """
    if not cams:
        return ()

    if previous_cam == "" and previous_profile == "":
        index_curr_cam = 0
        index_curr_profile = 0
    else:
        index_curr_cam = cams.index(previous_cam)
        index_curr_profile = profiles.index(previous_profile)
        assert index_curr_cam > -1
        assert index_curr_profile > -1

    for index_cam in range(index_curr_cam, len(cams)):
        # перебор профилей камеры - начинаем со следующего после текущего
        for index_profile in range(index_curr_profile, len(profiles)):
            if profiles[index_profile] == previous_profile and cams[index_cam] == previous_cam:
                continue
            cam = cams[index_cam]
            profile = profiles[index_profile]
            return cam, profile
    return ()


def get_next_cam_json(path_to_db: str,  statistic: Statistic, servers: tuple, cams: tuple, profiles: tuple,
                      previous_info: tuple) -> tuple:
    """Функция возвращает json следующей камеры, основываясь на предыдущей камеры
       из списков отфильтрованных камер для текущего сервера из списка отфильтрованных серверов.

    Первый запуск функции должен быть с параметрами:
    (путь к бд, статистика, список серверов, список камер, список профилей)

    :param path_to_db: путь к файлу БД;
    :param statistic: объект класса Statistic;
    :param servers: список серверов;
    :param cams: список камер;
    :param profiles: список профилей;
    :param previous_info: информация о предыдущей камеры (тот же контейнер, что эта функция вернула в крайний раз).

    :return: кортеж: 0 - json камеры, 1 - имя сервера, 2 - имя камеры, 3 - имя профиля.
    - если вернется {}, "", "", "", [] - то это признак окончания полного прохода
    - если вернется{}, имя_сервера, "", "", [] - то значит был переход на следующий сервер и список камер нужно
    получить новый
    """
    logger = statistic.get_log().get_logger("scripts/common/tools")
    logger.info("was called (path_to_db: str,  statistic: Statistic, servers: tuple, cams: tuple, profiles: tuple,"
                "previous_info: str)")
    logger.debug("params (" + path_to_db + ", stat_obj, " + str(servers) + ", " + str(cams) + ", " + str(profiles)
                 + ", " + str(previous_info) + ")")

    if not previous_info:
        current_server = servers[0]
        next_cam = get_next_cam(cams, profiles)
    else:
        current_server = previous_info[1]
        next_cam = get_next_cam(cams, profiles, previous_cam=previous_info[2], previous_profile=previous_info[3])

    if not cams:
        statistic.append_error("Список отфильтрованных камер для сервера " + current_server + " пуст!", "БД")

    if not next_cam:
        index_current_server = servers.index(current_server)
        if index_current_server == len(servers) - 1:
            return ()
        return {}, servers[index_current_server + 1], "", ""

    current_cam = next_cam[0]
    current_profile = next_cam[1]

    logger.info("current operation: get_cam_json")
    logger.info("call func db.get_cam_json(path_to_db, key1, key2, key3)")
    logger.debug("params (" + path_to_db + ", " + current_server + ", " + current_cam + ", " + current_profile + ")")
    json_cam: dict = db.get_cam_json(path_to_db, current_server, current_cam, current_profile, statistic)

    return json_cam, current_server, current_cam, current_profile
