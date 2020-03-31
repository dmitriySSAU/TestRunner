import time

from lib.log_and_statistic import log
from lib.log_and_statistic.statistics import Statistic

from lib.client.soapClient import SoapClient

from scripts.ws import ptz as ws
from scripts.common import tools


def compare_coordinates(first_coordinate: int, second_coordinate: int, inaccuracy: int = 0) -> bool:
    """Функция сравнения двух координат.

    :param first_coordinate: первая координата
    :param second_coordinate: вторая координата
    :param inaccuracy: погершность равенства координат

    :return: True - равны; False - различны.
    """
    logger = log.get_logger("scripts/tools/ptz")
    logger.info("was called (first_coordinate: int, second_coordinate: int, inaccuracy: int = 0)")
    logger.debug("with params (" + str(first_coordinate) + ", " + str(second_coordinate) + ", " + str(inaccuracy) + ")")

    if first_coordinate == second_coordinate:
        return True
    else:
        if inaccuracy == 0:
            return False

        if first_coordinate > second_coordinate:
            for inaccuracy_ in range(1, inaccuracy + 1):
                second_coordinate += 1
                if first_coordinate == second_coordinate:
                    return True
        else:
            for inaccuracy_ in range(1, inaccuracy + 1):
                first_coordinate += 1
                if first_coordinate == second_coordinate:
                    return True

        return False


def get_coordinates(client: SoapClient, login: str, password: str, key2: str, statistic: Statistic) -> dict:
    """Функция для получения координат (использует ws метод ptzclient:Command)

    :param client: объект soap клиента
    :param login: логин пользователя
    :param password: пароль пользователя
    :param key2: имя камеры
    :param statistic: объект класса Statistic

    :return: словарь с координатами (ключи pan и tilt)
    """
    logger = log.get_logger("scripts/tools/ptz")
    logger.info("was called (client: SoapClient, login: str, password: str, key2: str)")
    logger.debug("with params (client_obj, " + login + ", " + password + ", " + key2 + ")")

    logger.info("call ptzclient_command_simple()")
    log.print_all("получение старых координат...")
    logger.info("getting old coordinates")
    query_all_result = ws.ptzclient_command_simple(client, key2, login, password, False, 0, 0, 0, 0, 0, 0, True, 0, 0,
                                                   -1, -1, False)
    log.print_all("ws 'ptzclient:Command[QueryAll=True]' выполнен успешно!")
    logger.info("ws method 'ptzclient:Command[QueryAll=True]' was executed successfully!")

    tools.check_types(["old_coordinates['result'][0]"], [query_all_result["result"][0]], [dict], statistic)
    is_old_coordinates = tools.check_keys_exist(query_all_result["result"][0], ["pan", "tilt", "timecoords"],
                                                'old_coordinates["result"][0]', False, statistic)
    old_timecoords = 0
    if is_old_coordinates:
        old_pan = query_all_result["result"][0]["pan"]
        old_tilt = query_all_result["result"][0]["tilt"]
        old_timecoords = query_all_result["result"][0]["timecoords"]
        logger.debug("old_pan: " + str(old_pan) + ", old_tilt: " + str(old_tilt) + ", old_timecoords: "
                     + str(old_timecoords))

    count_coordinates_missing = 0
    while True:
        logger.info("call ptzclient_command_simple()")
        log.print_all("получение текуших координат...")
        logger.info("getting current coordinates")
        current_coordinates = ws.ptzclient_command_simple(client, key2, login, password, False, 0, 0, 0, 0, 0, 0, True,
                                                          0, 0, -1, -1, False)
        log.print_all("ws 'ptzclient:Command[QueryAll=True]' выполнен успешно!")
        logger.info("ws method 'ptzclient:Command[QueryAll=True]' was executed successfully!")

        tools.check_types(["current_coordinates['result'][0]"], [current_coordinates["result"][0]], [dict], statistic)
        is_current_coordinates = tools.check_keys_exist(current_coordinates["result"][0], ["pan", "tilt"],
                                                        'current_coordinates["result"][0]', False, statistic)
        if is_current_coordinates is False:
            count_coordinates_missing += 1
            if count_coordinates_missing == 3:
                statistic.append_error("Получение координат завершилось с ошибкой!", "НЕТ_КООРДИНАТ", False)
                break
            continue
        current_timecoords = current_coordinates["result"][0]["timecoords"]

        if is_old_coordinates and current_timecoords != old_timecoords or is_old_coordinates is False:
            current_pan = current_coordinates["result"][0]["pan"]
            current_tilt = current_coordinates["result"][0]["tilt"]
            logger.debug("current_pan: " + str(current_pan) + ", current_tilt: " + str(current_tilt))

            return {
                "pan": current_pan,
                "tilt": current_tilt
            }


def turn(client: SoapClient, login: str, password: str, key1: str, key2: str, key3: str, cmd: str,
         statistic: Statistic) -> bool:
    """Функция для поворота камеры в нужную сторону (right, left, up, down) с использованием нужного ws метода.
        либо ptzserver:command (key1 и key3 != ""), либо ptzclient:command (key1 и key3 == "").

    :param client: объект soap клиентя
    :param login: логин пользователя
    :param password: пароль пользователя
    :param key1: имя сервера. Если нужно осуществить поворот с помощью ws метода ptzserver:command, то key1 должен
    быть обязательно заполнен (!= "")
    :param key2: имя камеры
    :param key3: профиль камеры. Если нужно осуществить поворот с помощью ws метода ptzserver:command, то key3 должен
    быть обязательно заполнен (!= "")
    :param cmd: направление поворота - right, left, up, down
    :param statistic: объект класса Statistic
    :return: флаг успешности поворота
    """
    logger = log.get_logger("scripts/tools/ptz")
    logger.info("was called (client: SoapClient, login: str, password: str, key1: str, key2: str, key3: str, cmd: str)")
    logger.debug("with params (client_obj, " + login + ", " + password + ", " + key1 + ", " + key2 + ", " + key3 +
                 ", " + cmd + ")")
    left = 0
    right = 0
    up = 0
    down = 0
    if cmd == "left":
        left = 70
    elif cmd == "right":
        right = 70
    elif cmd == "up":
        up = 70
    elif cmd == "down":
        down = 70

    coordinates = get_coordinates(client, login, password, key2, statistic)
    if cmd == "up" or cmd == "down":
        current_coordinate = coordinates["tilt"]
    else:
        current_coordinate = coordinates["pan"]

    log.print_all("поворот " + cmd + "...")
    logger.info("turning " + cmd)
    if key1 == "" and key3 == "":
        ws.ptzclient_command_simple(client, key2, login, password, False, left, right, up, down, 0, 0, False, 0, 0, -1,
                                    -1, False)
    log.print_all("ws 'ptzclient:Command[" + cmd + "=70]' отправлен...")
    logger.info("ws method 'ptzclient:Command[" + cmd + "=70]' was sent")

    ws.ptzclient_command_simple(client, key2, login, password,
                                True, 0, 0, 0, 0, 0, 0, False, 0, 0, -1, -1, False)  # отправка остановки
    log.print_all("ws 'ptzclient:Command[" + cmd + "=0]' отправлен...")
    logger.info("ws method 'ptzclient:Command[" + cmd + "=0]' was sent")

    old_coordinate = current_coordinate
    coordinates = get_coordinates(client, login, password, key2, statistic)
    if cmd == "up" or cmd == "down":
        current_coordinate = coordinates["tilt"]
    else:
        current_coordinate = coordinates["pan"]

    if compare_coordinates(old_coordinate, current_coordinate) is False:
        log.print_test("Поворот " + cmd + " успешно выполнен!")
        logger.info("turning " + cmd + " was executed successfully!")
        return True
    else:
        return False


def go_to_coordinate(client: SoapClient, login: str, password: str, key2: str, ws_method: str,
                     cmd: str, coordinate: int, statistic: Statistic, inaccuracy: int = 0) -> bool:
    """Функция перевода камеры в указанные координаты.

    :param client: объект soap клиентя
    :param login: логин пользователя
    :param password: пароль пользователя
    :param key2: имя камеры
    :param ws_method: через какой метод выполнять команду (ptzserver или ptzclient)
    :param cmd: команда
    :param coordinate: координаты
    :param statistic: объект класса Statistic
    :param inaccuracy точность
    :return: флаг успешности перехода
    """
    logger = log.get_logger("scripts/tools/ptz")
    logger.info("was called (client: SoapClient, login: str, password: str, key2: str, \
                cmd: str, coordinate: int, inaccuracy: int = 0)")
    logger.debug("with params (client_obj, " + login + ", " + password + ", " + key2 + ", " +
                 cmd + ", " + str(coordinate) + ", " + str(inaccuracy) + ")")

    pan_to = -1
    tilt_to = -1
    if cmd == "PanTo":
        pan_to = coordinate
    elif cmd == "TiltTo":
        tilt_to = coordinate
    else:
        statistic.append_error(cmd, "НЕВАЛИД_КОМАНДА_PTZ", True)

    if ws_method == "ptzclient":
        ws.ptzclient_command_simple(client, key2, login, password, False, 0, 0, 0, 0, 0, 0, False, 0, 0, pan_to,
                                    tilt_to, False)
        message = "ws 'ptzclient:Command[" + cmd + "=" + str(coordinate) + "]' отправлен..."
    elif ws_method == "ptzserver":
        ws.ptzserver_command_simple(client, key2, login, password, False, 0, 0, 0, 0, 0, 0, False, 0, 0,
                                    pan_to, tilt_to, False)
        message = "ws 'ptzserver:Command[" + cmd + "=" + str(coordinate) + "]' отправлен..."
    else:
        statistic.append_error(ws_method, "НЕВАЛИД_МЕТОД_PTZ", True)

    log.print_all(message)
    logger.info(message)
    time.sleep(1)

    coordinates = get_coordinates(client, login, password, key2, statistic)
    if cmd == "TiltTo":
        current_coordinate = coordinates["tilt"]
    else:
        current_coordinate = coordinates["pan"]

    if compare_coordinates(coordinate, current_coordinate, inaccuracy):
        log.print_test(cmd + " " + str(coordinate) + " выполнена успешно!")
        logger.info(cmd + " " + str(coordinate) + " was executed successfully!")
        return True
    else:
        return False
