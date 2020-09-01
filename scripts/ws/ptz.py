from lib.log_and_statistic import log
from lib.log_and_statistic.statistic import Statistic

from lib.client.soapClient import SoapClient

from requests_patterns.ws import ptz as pattern


def ptzclient_command_simple(client: SoapClient, key2: str, token: str, statistic: Statistic, stop: bool = False,
                             left: int = 0, right: int = 0, up: int = 0, down: int = 0, zoom_in: int = 0,
                             zoom_out: int = 0, query_all: bool = False, go_to_preset: int = 0, set_preset: int = 0,
                             pan_to: int = -1, tilt_to: int = -1, home: bool = False) -> dict:
    """

    :param client:
    :param key2:
    :param token:
    :param statistic
    :param stop:
    :param left:
    :param right:
    :param up:
    :param down:
    :param zoom_in:
    :param zoom_out:
    :param query_all:
    :param go_to_preset:
    :param set_preset:
    :param pan_to:
    :param tilt_to:
    :param home:

    :return:
    """
    logger = statistic.get_log().get_logger("scripts/ws/ptz")
    logger.info("was called (client: SoapClient, key2: str, token: str, statistic: Statistic, stop: bool, left: int, \
                             right: int, up: int, down: int, zoom_in: int, zoom_out: int, query_all: bool, \
                             go_to_preset: int, set_preset: int, pan_to: int, tilt_to: int, home: bool)")
    logger.debug("params (client_obj, " + key2 + ", " + token + ", statistic_obj, " + str(stop) + ", " + str(left) +
                 ", " + str(right) + ", " + str(up) + ", " + str(down) + ", " + str(zoom_in) + ", " + str(zoom_out) +
                 ", " + str(query_all) + ", " + str(go_to_preset) + ", " + str(set_preset) + ", " + str(pan_to) +
                 ", " + str(tilt_to) + ", " + str(home) + ")")

    params, sysparams, method = pattern.ptzclient_command_simple(key2, token, stop, left, right, up, down, zoom_in,
                                                                 zoom_out, query_all, go_to_preset, set_preset, pan_to,
                                                                 tilt_to, home)

    response = client.call_method2(method, params, sysparams, [0])
    logger.info("ws method ptzclient:Command was executed successfully!")
    statistic.append_info("ptzclient:Command выполнен успешно", "WS_МЕТОД")

    return response


def ptzserver_command_simple(client: SoapClient, key2: str, token: str, statistic: Statistic, stop: bool = False,
                             left: int = 0, right: int = 0, up: int = 0, down: int = 0, zoom_in: int = 0,
                             zoom_out: int = 0, query_all: bool = False, go_to_preset: int = 0, set_preset: int = 0,
                             pan_to: int = -1, tilt_to: int = -1, home: bool = False) -> dict:
    """

    :param client:
    :param key2:
    :param token:
    :param stop:
    :param left:
    :param right:
    :param up:
    :param down:
    :param zoom_in:
    :param zoom_out:
    :param query_all:
    :param go_to_preset:
    :param set_preset:
    :param pan_to:
    :param tilt_to:
    :param home:

    :return:
    """
    logger = statistic.get_log().get_logger("scripts/ws/ptz")
    logger.info("was called (client: SoapClient, key2: str, token: str, statistic: Statistic, stop: bool,\
                             left: int, right: int, up: int, down: int, zoom_in: int, zoom_out: int, query_all: bool,\
                             go_to_preset: int, set_preset: int, pan_to: int, tilt_to: int, home: bool)")
    logger.debug("params (client_obj, " + key2 + ", " + token + ", statistic_obj" + str(stop) + ", " + str(left) +
                 ", " + str(right) + ", " + str(up) + ", " + str(down) + ", " + str(zoom_in) + ", " + str(zoom_out) +
                 ", " + str(query_all) + ", " + str(go_to_preset) + ", " + str(set_preset) + ", " + str(pan_to) +
                 ", " + str(tilt_to) + ", " + str(home) + ")")

    params, sysparams, method = pattern.ptzserver_command_simple(key2, token, stop, left, right, up, down, zoom_in,
                                                                 zoom_out, query_all, go_to_preset, set_preset, pan_to,
                                                                 tilt_to, home)

    response = client.call_method2(method, params, sysparams, [0])
    logger.info("ws method ptzserver:Command was executed successfully!")
    statistic.append_info("ptzserver:Command выполнен успешно", "WS_МЕТОД")

    return response


def ptzserver_list_profiles(client: SoapClient, token: str, statistic: Statistic) -> list:
    logger = statistic.get_log().get_logger("scripts/ws/ptz")
    logger.info("was called (client: SoapClient, token: str, statistic: Statistic)")
    logger.debug("with params (client_obj, " + token + ", stat_obj)")

    params, sysparams, method = pattern.ptzserver_list_profiles(token)
    response = client.call_method2(method, params, sysparams, [0])

    logger.info("ws method " + method + " was executed successfully!")
    statistic.append_info(method + " выполнен успешно!", "WS_МЕТОД")

    if not response["result"] or response["result"] == [{}]:
        statistic.append_error("Список PTZ камер пуст!", "НЕТ PTZ КАМЕР")
        return []

    return response["result"]
