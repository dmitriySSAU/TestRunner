from requests_patterns.web import profiles

from lib.log_and_statistic import log
from lib.client.soapClient import SoapClient
from lib.log_and_statistic.statistics import Statistic

from scripts.common import db, tools
from scripts.ws import server as ws_video_server


def set_key2(json_cam: dict, key2: str, statistic: Statistic) -> dict:
    """Меняет key2 в словаре json камеры при наличии соответсвующего ключа.

    :param json_cam: словарь с json графа (камеры)
    :param key2: новое имя камеры (ключ key2)
    :param statistic: объект класса Statistic

    :return: обновленный словарь json графа (камеры)
    """
    tools.check_keys_exist(json_cam, ['common'], "json_cam", True, statistic)
    tools.check_keys_exist(json_cam['common'], ['key2'], "json_cam['common']", True, statistic)

    json_cam['common']['key2'] = key2

    return json_cam


def set_id54(json_cam: dict, new_id54: int, statistic: Statistic) -> dict:
    """ Меняет id54 в словаре json камеры при наличии соответсвующего ключа (в network_5_4 и sender).

    :param json_cam: словарь с json графа (камеры)
    :param new_id54: новый id54 камеры
    :param statistic: объект класса Statistic

    :return: обновленный словарь json графа (камеры)
    """
    # заменяем id54 в network_5_4
    tools.check_keys_exist(json_cam, ['network_5_4'], 'json_cam', True, statistic)
    tools.check_types(['network_5_4'], [json_cam['network_5_4']], [list], statistic)
    tools.check_values(['network_5_4'], [json_cam['network_5_4']], [0], [">"], statistic)
    for index, network_5_4 in enumerate(json_cam['network_5_4']):
        tools.check_keys_exist(network_5_4, ['iv54server'], 'network_5_4["' + str(index) + '"]', True, statistic)
        tools.check_keys_exist(network_5_4['iv54server'], ['ID_54'], 'network_5_4["' + str(index) + '"]["iv54server"]',
                               True, statistic)
        tools.check_keys_exist(network_5_4['iv54server']['ID_54'], ['_value'],
                               'network_5_4["' + str(index) + '"]["iv54server"]["ID_54"]', True, statistic)
        json_cam['network_5_4'][index]['iv54server']['ID_54']['_value'] = new_id54

    # заменяем id54 в sender
    tools.check_keys_exist(json_cam, ['sender'], 'json_cam', True, statistic)
    tools.check_types(['sender'], [json_cam['sender']], [list], statistic)
    tools.check_values(['sender'], [json_cam['sender']], [0], [">"], statistic)
    for index, sender in enumerate(json_cam['sender']):
        tools.check_keys_exist(sender, ['_type'], 'sender["' + str(index) + '"]', True, statistic)
        tools.check_keys_exist(sender['_type'], ['_value'], 'sender["' + str(index) + '"]["_type"]', True, statistic)

        tools.check_keys_exist(sender['_type']['_value'], ['id'], 'sender["' + str(index) + '"]["_type"]["_value"]',
                               True, statistic)
        tools.check_keys_exist(sender['_type']['_value']['id'], ['_value'],
                               'sender["' + str(index) + '"]["_type"]["_value"]["id"]', True, statistic)
        json_cam['sender'][index]['_type']['_value']['id']['_value'] = new_id54

    return json_cam


def get_free_id54(list_id54: list) -> int:
    """Получение свободного id54.

    :param list_id54: список существующих id54 в БД

    :return: свободный id54
    """
    logger = log.get_logger("scripts/common/graph")
    logger.info("was called(list_id54)")
    logger.debug("with params(" + str(list_id54) + ")")

    free_id54 = 1
    while True:
        got_free_id = True
        for id54 in list_id54:
            if free_id54 == id54:
                got_free_id = False
                free_id54 += 1
                break
        if got_free_id:
            logger.debug("free id54: " + str(free_id54))
            return free_id54


def get_free_key2(list_key2, id54):
    """
    Get free key2 for creating graph

    :param list_key2: список существующих камер в БД.
    :param id54: id54 для новой камеры (будет добавен к имени)

    :return: свободный key2
    """
    logger = log.get_logger("scripts/common/graph")
    logger.info("call func get_free_key2(list_key2, id54)")
    logger.debug("get_free_key2(" + str(list_key2) + ", " + str(id54) + ")")

    key2_id = id54
    free_key2 = "py_test_cam_" + str(key2_id)

    while True:
        got_free_key2 = True
        for key2 in list_key2:
            if free_key2 == key2:
                got_free_key2 = False
                key2_id += 1
                break

        if got_free_key2:
            logger.debug("free key2: " + str(free_key2))
            return free_key2


def insert_graphs_to_db(client: SoapClient, login: str, password: str, path_to_db: str, json_: dict, key1: str,
                        key3: str, count: int, statistic: Statistic) -> list:
    """ Добавляет в БД указанное количество графов c указанным json.

    Соблюдает уникальность key2 и id54 в БД.

    :param client: объект клиента класса SoapClient
    :param login: логин пользователя для ws метода
    :param password: пароль пользователя для ws метода
    :param path_to_db: путь к БД
    :param json_: json графа (камеры)
    :param key1: имя сервера
    :param key3: профиль key3
    :param count: количество графов для добавления в БД
    :param statistic: объект класса Statistic

    :return: список key2 добавленных камер
    """
    logger = log.get_logger("scripts/common/graph")
    logger.info("was called (client: SoapClient, login: str, password: str, path_to_db: str, json_: dict, key1: str," +
                "key3: str, count: int, statistic: Statistic)")

    logger.info("call func db.get_lists_id54_and_key2(path_to_db)")
    logger.debug("with params (" + path_to_db + ")")
    result = db.get_lists_key2_and_id54(path_to_db, key1, statistic)
    list_key2: list = result[0]
    list_id54: list = result[1]
    logger.debug("list_key2: " + str(list_key2))
    logger.debug("list_id54: " + str(list_id54))

    list_new_key2: list = []
    for graph in range(count):
        free_id54 = get_free_id54(list_id54)
        free_key2 = get_free_key2(list_key2, free_id54)
        logger.debug("free_id54: " + str(free_id54))
        logger.debug("free_key2: " + str(free_key2))

        list_id54.append(free_id54)
        list_key2.append(free_key2)
        list_new_key2.append(free_key2)

        set_key2(json_, free_key2, statistic)
        set_id54(json_, free_id54, statistic)

        setid = db.insert_new_cam(path_to_db, key1, free_key2, key3, json_, statistic)
        logger.info("Вставка камеры '" + free_key2 + "' в БД выполена успешно!")
        log.print_all("Вставка камеры '" + free_key2 + "' в БД выполена успешно!")

        ws_video_server.reload_graph(client, setid, login, password)
        logger.info("Перезагрузка графа в процессе по камере " + free_key2 + " выполнена успешно!")
        log.print_all("Перезагрузка графа в процессе по камере " + free_key2 + " выполнена успешно!")

    return list_new_key2


def create_json_from_profiles(key1: str, extra_blocks_path: str, path_to_video: str, statistic: Statistic) -> dict:
    """Получение профилей common, media, muxer, iv54server, sender и доп. блоков из файла.

    :param key1: имя видеосервера
    :param extra_blocks_path: файл с доп. блоками для присоединение к базовым блокам
    :param path_to_video: Путь до источника видео
    :param statistic: объект класса Statistic
    """
    logger = log.get_logger("scripts/common/graph")

    common: dict = profiles.get_common_dict(key1, "1")
    media: dict = profiles.get_device_media_dict(path_to_video)
    muxer: dict = profiles.get_muxer_dict("trackSource")
    network_5_4: dict = profiles.get_network_5_4_dict(1)
    sender: dict = profiles.get_sender_dict(1)
    dicts = [common, media, muxer, network_5_4, sender]

    logger.info("call func tools.open_json_file(path, logger)")
    logger.debug("tools.open_json_file(" + extra_blocks_path + ", logger)")
    json_blocks: dict = tools.open_json_file(extra_blocks_path, statistic)
    logger.debug("dict_json_block: " + str(json_blocks))

    for block in json_blocks:
        dicts.append(
            {
                block: json_blocks[block]
            }
        )
    logger.info("current operation: connect profiles")
    logger.info("call func tools.get_full_dict(list)")
    logger.debug("tools.get_full_dict(" + str(dicts) + ")")

    return tools.get_full_dict(dicts)


def get_plugin_type(section: dict, statistic: Statistic) -> str:
    """Функция получение типа плгина из секции блока json камеры.

    :param section: секция json
    :param statistic: объект класса Statistic
    :return: тип плагина
    """
    logger = log.get_logger("scripts/common/graph")
    logger.info("was called func get_plugin_type(section: dict, statistic: Statistic)")
    logger.debug("with params (" + str(section) + ")")

    tools.check_keys_exist(section, ["_type"], "section", True, statistic)
    tools.check_keys_exist(section['_type'], ["_value"], "section['_type']", True, statistic)

    return section['_type']['_value']


def is_plugin_exist(block: dict, plugin_type: str, statistic: Statistic) -> int:
    """Проверка существования секции с указанном типом в блоке.

    :param block: блок json
    :param plugin_type: тип секции (плагина)
    :param statistic: объект класса Statistic
    :return: индекс плагина в блоке
    """
    logger = log.get_logger("scripts/common/graph")
    logger.info("was called (block: dict, plugin_type: str, statistic: Statistic)")
    logger.debug("with params (" + str(block) + ", " + plugin_type + ")")

    section_index = -1
    for index, section_from_file in enumerate(block):
        if plugin_type == get_plugin_type(section_from_file, statistic):
            section_index = index
            break
    return section_index


def check_detection_regions_keys(json_detector: dict, statistic: Statistic) -> bool:
    """Проверка существования основных ключей для зоны детектора.

    :param json_detector: json с секцией детектора
    :param statistic: объект класса Statistic
    :return: флаг корректности
    """
    logger = log.get_logger("scripts/common/graph")
    logger.info("was called (dict_json_detector)")
    logger.debug("with params (" + str(json_detector) + ")")

    detector_name = get_plugin_type(json_detector, statistic)

    if tools.check_keys_exist(json_detector[detector_name], ['detection_regions'],
                              detector_name, False, statistic) is False:
        return False

    if tools.check_keys_exist(json_detector[detector_name]['detection_regions'], ['square'],
                              detector_name, False, statistic) is False:
        return False

    if tools.check_keys_exist(json_detector[detector_name]['detection_regions']['square'], ['_value'],
                              detector_name, False, statistic) is False:
        return False

    return True


def get_detection_regions_from_detector_json(json_detector: dict, statistic: Statistic) -> list:
    """Получение списках всех зон детектора.

    :param json_detector: json с секцией детектора
    :param statistic: объект класса Statistic
    :return: список имен зон
    """
    logger = log.get_logger("scripts/common/graph")
    logger.info("was called (json_detector: dict, statistic: Statistic)")
    logger.debug("with params (" + str(json_detector) + ")")

    if check_detection_regions_keys(json_detector, statistic) is False:
        return []

    detector_name = get_plugin_type(json_detector, statistic)
    zones: list = json_detector[detector_name]['detection_regions']['square']['_value']
    tools.check_types(["zones"], [zones], [list], statistic)

    return zones


def get_region_name(region: dict, statistic: Statistic) -> str:
    """Получение имени зоны из указанного json зоны.

    :param region: json зоны
    :param statistic: объект класса Statistic
    :return: имя зоны (региона)
    """
    logger = log.get_logger("scripts/common/graph")
    logger.info("was called (region: dict, statistic: Statistic)")
    logger.debug("with params (" + str(region) + ")")

    if tools.check_keys_exist(region, ['name'], 'region', False, statistic) is False:
        return ""

    if tools.check_keys_exist(region['name'], ['_value'], 'region["name"]', False, statistic) is False:
        return ""

    return region['name']['_value']


def get_region_from_detector_json(json_detector: dict, region_name: str, statistic: Statistic) -> tuple:
    """Получение индекса и json зоны из детектора по ее имени.

    :param json_detector: json с секцией детектора
    :param region_name: имя зоны
    :param statistic: объект класса Statistic
    :return: кортеж: 0 - индекс региона в списке зон, 1 - json зоны
    """
    logger = log.get_logger("scripts/common/graph")
    logger.info("was called (json_detector: dict, region_name: str, statistic: Statistic)")
    logger.debug("with params(" + str(json_detector) + ", " + region_name + ")")

    zones = get_detection_regions_from_detector_json(json_detector, statistic)
    for index, region in enumerate(zones):
        if get_region_name(region, statistic) == region_name:
            return index, region
    return -1, {}


def get_points_from_region(json_detector: dict, region_name: str, statistic: Statistic) -> dict:
    """Получение словаря со списком _points из указанной зоны детектора.

    :param json_detector: json с секцией детектора
    :param region_name: имя зоны
    :param statistic: объект класса Statistic
    :return: словарь со списком _points
    """
    logger = log.get_logger("scripts/common/graph")
    logger.info("was called (json_detector: dict, region_name: str, statistic: Statistic")
    logger.debug("get_points_from_region(" + str(json_detector) + ", " + region_name + ")")

    data = get_region_from_detector_json(json_detector, region_name, statistic)
    index_region = data[0]
    region = data[1]
    if index_region == -1:
        statistic.append_error("в " + region_name, "НЕТ_ЗОНЫ", False)
        return {}

    for first_lvl_key in region:
        if first_lvl_key == '_points':
            return {
                first_lvl_key: region[first_lvl_key]
            }
    return {}


def replace_region_on_cam_json(json_detector: dict, new_region: dict, only_points: bool, statistic: Statistic) -> dict:
    """Полное замены зоны на детекторе без проверки внутренних ключей.

    :param json_detector: json с секцией детектора
    :param new_region: словарь с новым регионом
    :param only_points: заменить только список points
    :param statistic: объект класса Statistic
    :return: новые словарь json детектора
    """
    logger = log.get_logger("scripts/common/graph")
    logger.info("was called (json_detector: dict, new_region: dict, only_points: bool, statistic: Statistic)")
    logger.debug("replace_region_on_cam_json(" + str(json_detector) + ", " + str(new_region) + ", "
                 + str(only_points) + ")")

    region_name = get_region_name(new_region, statistic)
    detector_name = get_plugin_type(json_detector, statistic)
    data = get_region_from_detector_json(json_detector, region_name, statistic)
    index_region = data[0]
    original_region = data[1]
    if index_region == -1:
        statistic.append_error("в " + region_name, "НЕТ_ЗОНЫ", False)
        return {}
    if only_points:
        if '_points' not in original_region:
            statistic.append_error("'_points' в '" + region_name + "'!", "НЕТ_КЛЮЧА", False)
        elif '_points' not in new_region:
            statistic.append_error("'_points' в новой зоне!", "НЕТ_КЛЮЧА", False)

        json_detector[detector_name]['detection_regions']['square']['_value'][index_region]['_points'] = \
            new_region['_points']
    else:
        json_detector[detector_name]['detection_regions']['square']['_value'][index_region] = new_region

    return json_detector


def replace_region_values_on_cam_json(json_detector: dict, region_name: str, new_region: dict,
                                      statistic: Statistic) -> dict:
    """Замена зоны по ключам (только существующие ключи).

    :param json_detector: json с секцией детектора
    :param region_name: имя зоны
    :param new_region: словарь с новым регионом
    :param statistic: объект класса Statistic
    :return:
    """
    logger = log.get_logger("scripts/common/tools")
    logger.info("was called (json_detector: dict, region_name: str, new_region: dict, statistic: Statistic")
    logger.debug("with params (" + str(json_detector) + ", " + region_name + ", " + str(new_region) + ")")

    detector_name = get_plugin_type(json_detector, statistic)
    data = get_region_from_detector_json(json_detector, region_name, statistic)
    index_region = data[0]
    region = data[1]
    if index_region == -1:
        statistic.append_error("в " + region_name, "НЕТ_ЗОНЫ", False)
        return {}

    for first_lvl_key in new_region.keys():

        if tools.check_keys_exist(region, [first_lvl_key], region_name + "[" + str(index_region) + "]",
                                  False, statistic) is False:
            continue
        # если данный ключ является отрисовкой зоны _points, то содержимое меняем
        # немного по другому
        if first_lvl_key == '_points':
            json_detector[detector_name]['detection_regions']['square']['_value'][index_region]['_points'] = \
                new_region['_points']
            txt_msg = "Замена ключа '_ points' в зоне '" + region_name + "[" + str(index_region) + \
                      "]' успешно выполнена!"
            logger.info(txt_msg)
            log.print_test(txt_msg)
            continue
        # для остальных ключей делаем замену в _value
        if tools.check_keys_exist(region[first_lvl_key], ['_value'], region_name + "[" + str(index_region) + "]",
                                  False, statistic) is False:
            continue
        if tools.check_keys_exist(new_region[first_lvl_key], ['_value'], first_lvl_key + " в новом регионе!",
                                  False, statistic) is False:
            continue

        json_detector[detector_name]['detection_regions']['square']['_value'][index_region][first_lvl_key]['_value'] \
            = new_region[first_lvl_key]['_value']
        txt_msg = "Замена ключа '" + first_lvl_key + "[_value]' в зоне '" + region_name + "[" + str(index_region) + \
                  "]' выполнена успешно!"
        logger.info(txt_msg)
        log.print_test(txt_msg)

    return json_detector
