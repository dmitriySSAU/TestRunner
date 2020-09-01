from lib.client.soapClient import SoapClient

from lib.log_and_statistic.statistic import Statistic

from scripts.common import tools

from requests_patterns.ws import listener_pinger as pattern

from scripts.tools import listener_pinger as tools_lp


def get_local_servers(client: SoapClient, token: str, direct_access: int, statistic: Statistic) -> dict:
    """WS метод listener_pinger_get_local_servers с проверками существования ключей и типов их значений.

    :param client: объект клиента класса SoapClient;
    :param token: токен авторизации4
    :param direct_access: параметр ws метода;
    :param statistic: объект класса Statistic.

    :return: response["result"][0]["data"]["string"].
    """
    logger = statistic.get_log().get_logger("scripts/ws/listener_pinger")
    logger.info("was called (client: SoapClient, token: str, direct_access: int, statistic: Statistic)")
    logger.debug("was called (client_obj, " + token + ", " + str(direct_access) + ", stat_obj)")

    params, sysparams, method = pattern.listener_pinger_get_local_servers(token, direct_access)
    response = client.call_method2(method, params, sysparams, [0])

    tools.check_types(["response['result'][0]"], [response['result'][0]], [dict], statistic)

    tools.check_keys_exist(response["result"][0], ['data', 'hash'], 'response["result"][0]', True, statistic)
    tools.check_types(['data', 'hash'], [response["result"][0]["data"], response["result"][0]["hash"]],
                      [dict, str], statistic)

    tools.check_keys_exist(response["result"][0]["data"], ['string'], 'response["result"][0]["data"]', True, statistic)
    tools.check_types(["response['result'][0]['data']['string']"], [response["result"][0]["data"]["string"]],
                      [dict], statistic)

    string = response["result"][0]["data"]["string"]
    tools_lp.listener_pinger_keys_verifier(string, statistic)

    logger.info("ws '" + method + "' выполнен успешно!")
    statistic.append_info(method + "' выполнен успешно!", "WS_МЕТОД")

    return string


def get_down_servers(client: SoapClient, token: str, direct_access: int, statistic: Statistic) -> dict:
    """WS метод listener_pinger_get_down_servers с проверками существования ключей и типов их значений.

    :param client: объект клиента;
    :param token: токен авторизации;
    :param direct_access: параметр ws метода;
    :param statistic: объект класса Statistic.

    :return: response["result"][0]["data"]["string"]
    """
    logger = statistic.get_log().get_logger("scripts/ws/listener_pinger")
    logger.info("was called (client: SoapClient, token: str, direct_access: int, statistic: Statistic)")
    logger.debug("with params (client_obj, " + token + ", " + str(direct_access) + ", stat_obj)")

    params, sysparams, method = pattern.listener_pinger_get_down_servers(token, direct_access)
    response = client.call_method2(method, params, sysparams, [0])

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

    logger.info("ws '" + method + "' выполнен успешно!")
    statistic.append_info(method + "' выполнен успешно!", "WS_МЕТОД")

    return response["result"][0]["data"]["string"]
