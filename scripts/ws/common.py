from datetime import datetime

from scripts.common import tools

from lib.log_and_statistic.statistic import Statistic

from lib.client.soapClient import SoapClient

from requests_patterns.ws import common as pattern


def get_current_server_time(client: SoapClient, token: str, statistic: Statistic) -> str:
    """Получение текущего времени сервера через скрытый ws метод time.

    :param client: экземпляр класса SoapClient;
    :param token: токен соединения;
    :param statistic: объект класса Statistic для ведения статистики ошибок и предупреждений.

    :return: строка в формате %Y.%m.%d %H:%M:%S:MS.
    """
    logger = statistic.get_log().get_logger("scripts/ws/common")
    logger.info("was called (client: SoapClient, token: str, statistic: Statistic)")
    logger.debug("params (client_obj, " + token + ", stat_obj)")

    params, sysparams, method = pattern.time(token)
    response_json = client.call_method2(method, params, sysparams, [0])
    tools.check_keys_exist(response_json["result"][0], ['iso'], '"result"[0]', True, statistic)

    current_date_utc = response_json["result"][0]['iso']
    current_date = str(datetime.strptime(current_date_utc, '%Y-%m-%dT%H:%M:%S.%fZ'))[:-3]
    # current_date = str(datetime.strptime(current_date_utc, '%Y.%m.%d-%H:%M:%S') + timedelta(hours=4))
    logger.info("ws '" + method + "' выполнен успешно!")
    statistic.append_info(method + "' выполнен успешно!", "WS_МЕТОД")

    return current_date


def get_plugin_info(client: SoapClient, token: str, path: str, name: str, statistic: Statistic) -> dict:
    """Получение информации о плагине через метод ws plugin_info:GetInfo

    :param client: экземпляр класса SoapClient;
    :param token: токен соединения;
    :param path: путь к плагину;
    :param name: имя плагина;
    :param statistic: объект класса Statistic для ведения статистики ошибок и предупреждений.

    :return: строка вида "Version " + version + "\n" + "User " + user + "\n" + "Build "+ build_date + "\n"
    """
    logger = statistic.get_log().get_logger("scripts/ws/common")
    logger.info("was called (client: SoapClient, token: str, path: str, name: str, statistic: Statistic)")
    logger.debug("params (client_obj, " + token + ", " + path + ", " + name + ", " + "stat_obj)")

    params, sysparams, method = pattern.plugin_info(token, name, path)
    response_json = client.call_method2(method, params, sysparams, [0])
    tools.check_keys_exist(response_json["result"][0], ['version', 'user', 'build'], '"result"[0]', True, statistic)

    logger.info("ws '" + method + "' выполнен успешно!")
    statistic.append_info(method + "' выполнен успешно!", "WS_МЕТОД")

    return response_json["result"][0]
