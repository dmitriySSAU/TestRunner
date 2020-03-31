import time
import json
import configparser
from zeep import Client
from zeep.exceptions import TransportError
from zeep.plugins import HistoryPlugin
from requests.exceptions import ConnectionError

from lib.log_and_statistic.statistics import Statistic
from lib.log_and_statistic import log
from scripts.common import tools


class SoapClient:
    """Класс для отправки/приема сообщений по протоколу SOAP

    """
    def __init__(self, ip: str, port: str, statistic: Statistic):
        self._statistic = statistic
        self._logger = log.get_logger("client\\soapClient")

        self._ip = ip
        self._port = port
        config = configparser.ConfigParser()
        config.read(log.path + "\\runner.conf")
        self._request_ws_pause = config.get("ws", "pause")

    def get_request_pause(self) -> int:
        """Получение значения паузы между ws запросами

        :return: пауза
        """
        return self._request_ws_pause

    def set_request_pause(self, pause: int) -> None:
        """Установка значения паузы между запросами

        :param pause: пауза
        """
        self._request_ws_pause = pause

    def call_method2(self, method: str, params: dict, sysparams: dict, user_code_capture: bool) -> dict:
        """Метод отправки сообщения и приема ответа по протоколу SOAP.

        :param method: имя ws метода
        :param params: параметры метода
        :param sysparams: системные параметры
        :param user_code_capture: флаг проверки ключа user_code на равенство нулю
        :return: словарь, полученный из json ответа
        """
        self._logger.info("was called (method: str, params: dict, sysparams: dict, user_code_capture: bool)")
        self._logger.debug("with params(" + method + ", " + str(params) + ", " + str(sysparams) + ", " +
                           str(user_code_capture))

        history = HistoryPlugin()
        url = 'http://' + self._ip + ':' + self._port + '/axis2/services/Iv7Server/?wsdl'
        try:
            log.print_all("\n[ЗАПРОС]")
            log.print_all("    Отправка: POST")
            log.print_all("    URL: " + url)
            log.print_all("    WS метод: " + method)
            log.print_all("    Параметры: " + str(params))

            time.sleep(float(self._request_ws_pause))
            client = Client(url, plugins=[history])
            start_time = time.time()
            response = client.service.CallMethod2(
                method, json.dumps(params), json.dumps(sysparams))
            response_time = round((time.time() - start_time) * 1000)

            self._logger.info("response received")
            self._logger.debug("response: " + str(response))

            headers = history.last_received['http_headers']
            size = headers['Content-Length']
            self._print_response_info(url, size, response_time)

            response_json = json.loads(response)
            tools.check_keys_exist(response_json, ['user_code', 'result'], 'response_json', True, self._statistic)
            tools.check_types(["response_json['result']"], [response_json["result"]], [list], self._statistic)

            if not response_json["result"]:
                self._statistic.append_error("Ключ 'result' пустой!", "WS_ОТВЕТ", True)

            if response_json["user_code"] == 0:
                return response_json

            if user_code_capture is False:
                return response_json

            if 'user_msg' in response_json:
                self._statistic.append_error("Значение 'user-code': " + str(response_json["user_code"]) +
                                             "... требуется 0. Значение 'user_msg': " + response_json["user_msg"],
                                             "WS_ОТВЕТ", True)

            if 'user_msg' in response_json['result'][0]:
                self._statistic.append_error("Значение 'user-code': " + str(response_json['result'][0]["user_code"])
                                             + "... требуется 0. Значение 'user_msg': " +
                                             response_json['result'][0]["user_msg"], "WS_ОТВЕТ", True)

            self._statistic.append_error("Значение 'user-code': " + str(response_json["user_code"])
                                         + "... требуется 0.", "WS_ОТВЕТ", True)

        except ConnectionError:
            self._statistic.append_error("Веб сервис не доступен на " + url, "ПОДКЛЮЧЕНИЕ", False)
            self._logger.error("Unable connect to " + url)
            time.sleep(10)
            self.call_method2(method, params, sysparams, user_code_capture)
        except TransportError as e:
            self._statistic.append_error("Код статуса: " + e.status_code, "ПОДКЛЮЧЕНИЕ", False)
            self._logger.error("Status code is " + e.status_code)
            time.sleep(10)
            self.call_method2(method, params, sysparams, user_code_capture)
        except json.JSONDecodeError:
            self._statistic.append_error("Некорректный формат JSON!", "WS_ОТВЕТ", True)

    def _print_response_info(self, url: str, size: str, response_time: int):
        self._logger.info("Status code is 200")

        log.print_all("[ОТВЕТ]")
        log.print_all("    Статус: 200 ОК")
        log.print_all("    Размер: " + size + " Б")
        log.print_all("    Время ответа: " + str(response_time) + " мс\n")

        if response_time > 200:
            self._logger.error("Response time more than 200ms")
            self._statistic.append_warn("Response time is " + str(response_time), "WS_RESPONSE")
