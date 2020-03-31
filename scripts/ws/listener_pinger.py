from lib.log_and_statistic import log
from lib.client.soapClient import SoapClient
from lib.log_and_statistic.statistics import Statistic

from requests_patterns.ws import listener_pinger as pattern

from scripts.common import tools
from scripts.tools import listener_pinger as tools_lp


def get_local_servers(client: SoapClient, login: str, password: str, direct_access: int, statistic: Statistic) -> dict:
    """WS метод listener_pinger_get_local_servers с проверками существования ключей и типов их значений.

    :param client: объект клиента класса SoapClient
    :param login: логин пользователя
    :param password: пароль пользователя
    :param direct_access: параметр ws метода
    :param statistic: объект класса Statistic

    :return: response["result"][0]["data"]["string"]
    """
    logger = log.get_logger("scripts/ws/listener_pinger")
    logger.info("was called (client, login, password, direct_access)")
    logger.debug("was called (client_obj, " + login + ", " + password + ", " + str(direct_access) + ")")

    data = pattern.listener_pinger_get_local_servers(login, password, direct_access)

    response = client.call_method2(data[2], data[0], data[1], True)

    tools.check_types(["response['result'][0]"], [response['result'][0]], [dict], statistic)

    tools.check_keys_exist(response["result"][0], ['data', 'hash'], 'response["result"][0]', True, statistic)
    tools.check_types(['data', 'hash'], [response["result"][0]["data"], response["result"][0]["hash"]],
                      [dict, str], statistic)

    tools.check_keys_exist(response["result"][0]["data"], ['string'], 'response["result"][0]["data"]', True, statistic)
    tools.check_types(["response['result'][0]['data']['string']"], [response["result"][0]["data"]["string"]],
                      [dict], statistic)

    string = response["result"][0]["data"]["string"]
    tools_lp.listener_pinger_keys_verifier(string, statistic)

    logger.info("ws '" + data[2] + "' выполнен успешно!")
    log.print_all("ws '" + data[2] + "' выполнен успешно!")

    return string


def get_down_servers(client: SoapClient, login: str, password: str, direct_access: int, statistic: Statistic) -> dict:
    """WS метод listener_pinger_get_down_servers с проверками существования ключей и типов их значений.

    :param client: объект клиента
    :param login: логин пользователя
    :param password: пароль пользователя
    :param direct_access: параметр ws метода
    :param statistic: объект класса Statistic

    :return: response["result"][0]["data"]["string"]
    """
    logger = log.get_logger("scripts/ws/listener_pinger")
    logger.info("was called (client, login, password, direct_access)")
    logger.debug("was called (client_obj, " + login + ", " + password + ", " + str(direct_access) + ")")

    data = pattern.listener_pinger_get_down_servers(login, password, direct_access)

    response = client.call_method2(data[2], data[0], data[1], True)

    tools.check_types(["response['result'][0]"], [response["result"][0]], [dict], statistic)

    tools.check_keys_exist(response["result"][0], ['data', 'hash'], 'response["result"][0]', False, statistic)
    tools.check_types(['data', 'hash'], [response["result"][0]["data"], response["result"][0]["hash"]],
                      [dict, str], statistic)

    tools.check_keys_exist(response["result"][0]["data"], ['string'], 'response["result"][0]["data"]', False, statistic)
    tools.check_types(["response['result'][0]['data']['string']"], [response["result"][0]["data"]["string"]],
                      [dict], statistic)

    string = response["result"][0]["data"]["string"]
    tools_lp.listener_pinger_keys_verifier(string, statistic)

    for down_server in string["down_servers"]:
        for key in down_server:
            tools_lp.listener_pinger_keys_verifier(down_server[key], statistic)
            #if not down_server[key]["cams"]

    logger.info("ws '" + data[2] + "' выполнен успешно!")
    log.print_all("ws '" + data[2] + "' выполнен успешно!")

    return response["result"][0]["data"]["string"]
