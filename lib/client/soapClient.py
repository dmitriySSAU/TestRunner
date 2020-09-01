import time
import json

from zeep import Client
from zeep.plugins import HistoryPlugin
from zeep.exceptions import TransportError

from requests.exceptions import ConnectionError

from lib.log_and_statistic.statistic import Statistic

from scripts.common import tools


class SoapClient:
    """Класс для отправки/приема сообщений по протоколу SOAP

    """

    def __init__(self, ip: str, port: int, config: dict, statistic: Statistic):
        self._statistic = statistic
        self._logger = statistic.get_log().get_logger("client/soapClient")

        self._ip = ip
        self._port = port
        self._history = HistoryPlugin()
        self._url = 'http://' + self._ip + ':' + str(self._port) + '/axis2/services/Iv7Server/?wsdl'
        while True:
            try:
                self._client = Client(self._url, plugins=[self._history])
                break
            except ConnectionError:
                self._statistic.append_error("Сервис не доступен на " + self._url, "WS_ПОДКЛЮЧЕНИЕ")
                self._logger.error("Unable connect to " + self._url)
                time.sleep(5)

        self._request_ws_pause: float = config['ws']['pause']
        self._timeout: int = config['ws']['timeout']
        self._expected_response_time: float = config['ws']['expected_response_time']

    def get_request_pause(self) -> float:
        """Получение значения паузы между ws запросами

        :return: пауза
        """
        return self._request_ws_pause

    def set_request_pause(self, pause: float) -> None:
        """Установка значения паузы между запросами

        :param pause: пауза
        """
        self._request_ws_pause = pause

    def call_method2(self, method: str, params: dict, sysparams: dict, expected_user_codes: list) -> dict:
        """Метод отправки сообщения и приема ответа по протоколу SOAP.

        :param method: имя ws метода;
        :param params: параметры метода;
        :param sysparams: системные параметры;
        :param expected_user_codes: ожидаемые значения user_code.

        :return: словарь, полученный из json ответа.
        """
        self._logger.info("was called (method: str, params: dict, sysparams: dict, expected_user_code: int)")
        self._logger.debug("with params(" + method + ", " + str(params) + ", " + str(sysparams) + ", " +
                           str(expected_user_codes))

        try:
            time.sleep(self._request_ws_pause)

            self._statistic.append_info("\n    Отправка: POST\n" +
                                        "    URL: " + self._url + "\n" +
                                        "    WS метод: " + method + "\n" +
                                        "    Параметры: " + str(params), "WS_ЗАПРОС")

            sysparams['timeout'] = self._timeout
            start_time = time.time()
            response: str = self._client.service.CallMethod2(method, json.dumps(params), json.dumps(sysparams))
            response_time = round((time.time() - start_time) * 1000)

            self._logger.info("response received")
            self._logger.debug("response: " + str(response))

            headers: dict = self._history.last_received['http_headers']
            size: str = headers['Content-Length']
            self._print_response_info(method, size, response_time)

            response: dict = json.loads(response)
            if tools.check_keys_exist(response, ['user_code'], 'response', False, self._statistic) is False:
                tools.check_keys_exist(response, ['code'], 'response', True, self._statistic)
            tools.check_keys_exist(response, ['result'], 'response', True, self._statistic)
            tools.check_types(["response['result']"], [response["result"]], [list], self._statistic)

            user_code_msg = ""
            equal_user_codes = False
            if 'user_code' in response:
                for expected_user_code in expected_user_codes:
                    if response["user_code"] == expected_user_code:
                        equal_user_codes = True
                        break
                user_code_msg = "Значение 'user-code': " + str(response["user_code"]) + "! "
            else:
                equal_user_codes = True
            # иногда user_code может быть равен 0 (якобы все хорошо),
            # но есть ключ code, который может быть НЕ равен 0.
            code_msg = ""
            if 'code' in response:
                for expected_user_code in expected_user_codes:
                    if response['code'] == expected_user_code and equal_user_codes:
                        return response
                code_msg = "Значение 'code': " + str(response["code"]) + "! "
            elif equal_user_codes:
                return response
            self._logger.error("response: " + str(response))

            if 'user_msg' in response:
                self._statistic.append_error(user_code_msg + code_msg + "Требуется " + str(expected_user_codes) +
                                             ". 'user_msg': " + response["user_msg"], "WS_ОТВЕТ: " + method, True)
            if response['result'] and 'user_msg' in response['result'][0]:
                self._statistic.append_error(user_code_msg + code_msg + "Требуется " + str(expected_user_codes) +
                                             ". 'user_msg': " + response['result'][0]["user_msg"], "WS_ОТВЕТ: " +
                                             method, True)
            self._statistic.append_error(user_code_msg + code_msg + "Требуется " + str(expected_user_codes) + ".",
                                         "WS_ОТВЕТ: " + method, True)
        except ConnectionError:
            self._statistic.append_error("Сервис не доступен на " + self._url, "WS_ПОДКЛЮЧЕНИЕ")
            self._logger.error("Unable connect to " + self._url)
            time.sleep(5)
            return self.call_method2(method, params, sysparams, expected_user_codes)
        except TransportError as e:
            self._statistic.append_error("Код статуса: " + str(e.status_code), "WS_ПОДКЛЮЧЕНИЕ")
            self._logger.error("Status code is " + str(e.status_code))
            time.sleep(5)
            return self.call_method2(method, params, sysparams, expected_user_codes)
        except json.JSONDecodeError:
            self._statistic.append_error("Некорректный формат JSON!", "WS_ОТВЕТ", True)

    def _print_response_info(self, method: str, size: str, response_time: int):
        self._logger.info("Status code is 200")

        self._statistic.append_info("\n    Статус: 200 ОК\n" +
                                    "    Размер: " + size + " Б\n" +
                                    "    Время ответа: " + str(response_time) + " мс", "WS_ОТВЕТ: " + method)

        expected_time_ms = self._expected_response_time * 1000
        if response_time > expected_time_ms:
            self._logger.error("Response time more than " + str(expected_time_ms) + "ms")
            self._statistic.append_warn("Время ответа больше " + str(expected_time_ms) + "мс (" +
                                        str(response_time) + ")", "WS_ОТВЕТ: " + method)
