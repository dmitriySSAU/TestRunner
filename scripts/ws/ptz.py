from requests_patterns.ws import ptz
from lib.log_and_statistic import log
from lib.client.soapClient import SoapClient


# ws method ptzclient:Command with simple input params
def ptzclient_command_simple(client: SoapClient, key2: str, login: str, password: str, stop: bool, left: int,
                             right: int, up: int, down: int, zoom_in: int, zoom_out: int, query_all: bool,
                             go_to_preset: int, set_preset: int, pan_to: int, tilt_to: int, home: bool) -> dict:
    """

    :param client:
    :param key2:
    :param login:
    :param password:
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
    logger = log.get_logger("scripts/ws/ptz")
    logger.info("was called (client: SoapClient, key2: str, login: str, password: str, stop: bool, left: int, \
                             right: int, up: int, down: int, zoom_in: int, zoom_out: int, query_all: bool, \
                             go_to_preset: int, set_preset: int, pan_to: int, tilt_to: int, home: bool)")
    logger.debug("with params (client_obj, " + key2 + ", " + login + ", " + password + ", " + str(stop)
                 + ", " + str(left) + ", " + str(right) + ", " + str(up) + ", " + str(down) + ", " + str(zoom_in) +
                 ", " + str(zoom_out) + ", " + str(query_all) + ", " + str(go_to_preset) + ", " + str(set_preset) +
                 ", " + str(pan_to) + ", " + str(tilt_to) + ", " + str(home) + ")")

    data = ptz.ptzclient_command_simple(key2, login, password, stop, left, right, up, down, zoom_in, zoom_out,
                                        query_all, go_to_preset, set_preset, pan_to, tilt_to, home)

    response = client.call_method2(data[2], data[0], data[1], True)

    return response


def ptzserver_command_simple(client: SoapClient, key2: str, login: str, password: str, stop: bool,
                             left: int, right: int, up: int, down: int, zoom_in: int, zoom_out: int, query_all: bool,
                             go_to_preset: int, set_preset: int, pan_to: int, tilt_to: int, home: bool) -> dict:
    """

    :param client:
    :param key2:
    :param login:
    :param password:
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
    logger = log.get_logger("scripts/ws/ptz")
    logger.info("was called (client: SoapClient, key2: str, login: str, password: str, stop: bool,\
                             left: int, right: int, up: int, down: int, zoom_in: int, zoom_out: int, query_all: bool,\
                             go_to_preset: int, set_preset: int, pan_to: int, tilt_to: int, home: bool)")
    logger.debug("with params (client_obj, " + key2 + ", " + login + ", " + password + ", "
                 + str(stop) + ", " + str(left) + ", " + str(right) + ", " + str(up) + ", " + str(down) + ", "
                 + str(zoom_in) + ", " + str(zoom_out) + ", " + str(query_all) + ", " + str(go_to_preset) + ", "
                 + str(set_preset) + ", " + str(pan_to) + ", " + str(tilt_to) + ", " + str(home) + ")")

    data = ptz.ptzserver_command_simple(key2, login, password, stop, left, right, up, down, zoom_in,
                                        zoom_out, query_all, go_to_preset, set_preset, pan_to, tilt_to, home)

    response = client.call_method2(data[2], data[0], data[1], True)

    return response


def ptzserver_list_profiles(client: SoapClient, login: str, password: str) -> list:
    logger = log.get_logger("scripts/ws/ptz")
    logger.info("was called (client, login, password)")
    logger.debug("with params (client_obj, " + str(login) + ", " + str(password) + ')')

    data = ptz.ptzserver_list_profiles(login, password)

    response = client.call_method2(data[2], data[0], data[1], True)

    return response["result"]
