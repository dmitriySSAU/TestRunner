import time
import configparser

from lib.runner import initializer
from lib.client.soapClient import SoapClient

from lib.log_and_statistic import log
from lib.log_and_statistic.statistics import Statistic

from scripts.common import tools
from scripts.tools import listener_pinger as tools_lp

from scripts.ws import iv54 as ws_iv54
from scripts.ws import ptz as ws_ptz
from scripts.ws import listener_pinger as ws_lp


class TestServer:
    """Класс-обертка с тестами для сервера

    """
    def __init__(self):
        self._statistic = Statistic()
        self._full_json = {}
        self._logger = log.get_logger("test\\test_Server")

        config = configparser.ConfigParser()
        config.read(log.path + "\\runner.conf")
        self._ip = config.get("server", "ip")
        self._port = config.get("server", "port")
        self._login = config.get("user", "login")
        self._password = config.get("user", "password")
        self._current_test = ""

    def get_tests_methods(self) -> dict:
        """Получение указателей на методы тестов по их имени

        :return: словарь указателей
        """
        return {
            "test_listener_pinger_down_servers": self.test_listener_pinger_down_servers,
            "test_listener_pinger_ptz_status": self.test_listener_pinger_ptz_status
        }

    def setup(self):
        """Данный метод вызывается перед запуском каждого теста.

        """
        self._full_json = tools.open_json_file(log.path + '\\tests\\data\\Server.json', self._statistic)

    def teardown(self):
        """Данный метод вызывается по завершению каждого теста.

        """
        print("----------------------------------FINISH------------------------------------\n")

        self._logger.info("show error statistic")

        self._statistic.show_common_statistic()
        self._statistic.show_errors_statistic()
        self._statistic.show_warns_statistic()
        time.sleep(0.1)

    def test_listener_pinger_down_servers(self):
        """Тестирование ws метода listener_pinger:get_down_servers.

        Тест циклично с установленной переодичностью опрашивает метод down_servers, затем сравнивает результат с
        эталоном (либо из файла, либо самый первый вызов этого метода), затем по порядку вызывает ws методы
        listener_pinger:get_local_servers для всех серверов из эталона и сравнивает результаты с эталоном.
        """
        self._current_test = "test_listener_pinger_down_servers"
        self._logger.info("START TEST " + self._current_test)

        input_data = initializer.init_data(self._full_json, self._current_test, self._statistic)
        tools.check_keys_exist(input_data, ['template_path', 'period', 'iterations'], 'data', True, self._statistic)
        tools.check_types(['template_path', 'period', 'iterations'],
                          [input_data["template_path"], input_data["period"], input_data["iterations"]],
                          [str, int, int], self._statistic)

        client = SoapClient(self._ip, self._port, self._statistic)

        if input_data["template_path"] != "":
            template_down_servers: dict = tools.open_json_file(input_data["template_path"], self._statistic)
            template_down_servers = template_down_servers["result"][0]["data"]["string"]
            log.print_all("Получен шаблон из файла...")
        else:
            template_down_servers: dict = ws_lp.get_down_servers(client, self._login, self._password, 1, self._statistic)
            log.print_all("Получен шаблон из ws istener_pinger:get_down_servers...")

        self._statistic.set_common_statistic({
            "Всего итераций": input_data["iterations"],
            "Успешных итераций": 0
        })

        for iteration in range(input_data["iterations"]):
            local_servers: dict = ws_lp.get_local_servers(client, self._login, self._password, 1, self._statistic)
            if tools_lp.compare_local_servers(local_servers, template_down_servers, self._ip, self._statistic):
                log.print_test("ответ ws listener_pinger:get_local_servers корректен!")
            else:
                log.print_all("текущее время сервера: " + str(ws_iv54.get_current_server_time(client, self._statistic)))
                self._statistic.append_error("ответ ws listener_pinger:get_local_servers некорректен!", "КРИТ", True)

            down_servers: dict = ws_lp.get_down_servers(client, self._login, self._password, 1, self._statistic)

            if tools_lp.compare_down_servers(down_servers, template_down_servers, self._ip, self._statistic):
                log.print_test("ответ ws listener_pinger:get_down_servers корректен!")
            else:
                log.print_all("текущее время сервера: " + str(ws_iv54.get_current_server_time(client, self._statistic)))
                self._statistic.append_error("ответ ws listener_pinger:get_down_servers некорректен!", "КРИТ", True)

            time.sleep(input_data["period"])
            self._statistic.get_common_statistic()["Успешных итераций"] += 1

    def test_listener_pinger_ptz_status(self):
        """Тестирование ws методов listener_pinger:get_down_servers и listener_pinger:get_local_servers с целью
        проверки статусов ptz камер.

        Тест циклично с установленной переодичностью опрашивает методы local_servers и down_servers, проходит по каждым
        потенциально ptz камерам рутового (верхнего) сервера и проверяет статус ptz.

        """
        self._current_test = "test_listener_pinger_ptz_status"
        self._logger.info("START TEST " + self._current_test)

        input_data = initializer.init_data(self._full_json, self._current_test, self._statistic)
        key_names: list = ['template_path', 'period', 'iterations']
        tools.check_keys_exist(input_data, key_names, 'data', True, self._statistic)
        key_values: list = [input_data["template_path"], input_data["period"], input_data["iterations"]]
        tools.check_types(key_names, key_values, [str, int, int], self._statistic)

        client = SoapClient(self._ip, self._port, self._statistic)

        if input_data["template_path"] != "":
            template_ptz_list_profiles: dict = tools.open_json_file(input_data["template_path"], self._statistic)
            template_ptz_list_profiles: list = template_ptz_list_profiles["result"]
            log.print_all("Получен шаблон из файла...")
        else:
            template_ptz_list_profiles: list = ws_ptz.ptzserver_list_profiles(client, self._login, self._password)
            log.print_all("Получен шаблон из ws ptzserver:list_profiles...")

        if not template_ptz_list_profiles:
            self._statistic.append_error("Пустой список камер в шаблоне!", "ВХ_ДАННЫЕ", True)

        for iteration in range(input_data["iterations"]):
            local_servers: dict = ws_lp.get_local_servers(client, self._login, self._password, 1, self._statistic)
            if tools_lp.check_ptz_cams(local_servers["cams"], template_ptz_list_profiles, self._statistic):
                log.print_test("Статусы PTZ в ответе ws listener_pinger:get_local_servers корректны!")
            else:
                self._statistic.append_error("Статусы PTZ в ответе ws listener_pinger:get_local_servers некорректны!",
                                             "КРИТ", True)

            down_servers: dict = ws_lp.get_down_servers(client, self._login, self._password, 1, self._statistic)
            if tools_lp.check_ptz_cams(down_servers["cams"], template_ptz_list_profiles, self._statistic):
                log.print_test("Статусы PTZ в ответе ws listener_pinger:get_down_servers корректны!")
            else:
                self._statistic.append_error("Статусы PTZ в ответе ws listener_pinger:get_down_servers некорректны!",
                                             "КРИТ", True)

            time.sleep(input_data["period"])
