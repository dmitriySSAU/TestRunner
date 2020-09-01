import time

from lib.client.soapClient import SoapClient

from lib.log_and_statistic.statistic import Statistic

from scripts.common import tools
from scripts.tools import listener_pinger as tools_lp

from scripts.ws import ptz as ws_ptz
from scripts.ws import users as ws_users
from scripts.ws import listener_pinger as ws_lp


class TestServer:
    """Класс-обертка с тестами для сервера

    """
    def __init__(self, input_data: dict, config: dict, statistic: Statistic):
        self._statistic: Statistic = statistic
        self._logger = self._statistic.get_log().get_logger("test/test_QML")

        self._input_data: dict = input_data
        self._config: dict = config

        self._ip = config["server"]["ip"]
        self._port = config["server"]["ws_port"]
        self._login = config["user"]["login"]
        self._password = config["user"]["password"]

    def setup(self):
        """Данный метод вызывается перед запуском каждого теста.

        """
        pass

    def teardown(self):
        """Данный метод вызывается по завершению каждого теста.

        """
        pass

    def listener_pinger_down_servers(self):
        """Тестирование ws метода listener_pinger:get_down_servers.

        Тест циклично с установленной переодичностью опрашивает метод down_servers, затем сравнивает результат с
        эталоном (либо из файла, либо самый первый вызов этого метода), затем по порядку вызывает ws методы
        listener_pinger:get_local_servers для всех серверов из эталона и сравнивает результаты с эталоном.
        """

        ws_client = SoapClient(self._ip, self._port, self._config, self._statistic)
        token = ws_users.server_login(ws_client, self._login, self._password, self._statistic)

        if self._input_data["template_path"]:
            template_down_servers: dict = tools.open_json_file(self._input_data["template_path"], self._statistic)
            template_down_servers = template_down_servers["result"][0]["data"]["string"]
            self._statistic.append_info("Получен шаблон из файла...", "ИНФО")
        else:
            template_down_servers: dict = ws_lp.get_down_servers(ws_client, token, 1, self._statistic)
            self._statistic.append_info("Получен шаблон из ws istener_pinger:get_down_servers...", "ИНФО")

        for iteration in range(self._input_data["iterations"]):
            local_servers: dict = ws_lp.get_local_servers(ws_client, token, 1, self._statistic)
            if tools_lp.compare_local_servers(local_servers, template_down_servers, self._ip, self._statistic):
                self._statistic.append_success("ответ ws listener_pinger:get_local_servers корректен!", "СРАВНЕНИЕ")
            else:
                self._statistic.append_error("ответ ws listener_pinger:get_local_servers некорректен!", "КРИТ", True)

            down_servers: dict = ws_lp.get_down_servers(ws_client, token, 1, self._statistic)

            if tools_lp.compare_down_servers(down_servers, template_down_servers, self._ip, self._statistic):
                self._statistic.append_success("ответ ws listener_pinger:get_down_servers корректен!", "СРАВНЕНИЕ")
            else:
                self._statistic.append_error("ответ ws listener_pinger:get_down_servers некорректен!", "КРИТ", True)

            time.sleep(self._input_data["period"])

    def listener_pinger_ptz_status(self):
        """Тестирование ws методов listener_pinger:get_down_servers и listener_pinger:get_local_servers с целью
        проверки статусов ptz камер.

        Тест циклично с установленной переодичностью опрашивает методы local_servers и down_servers, проходит по каждым
        потенциально ptz камерам рутового (верхнего) сервера и проверяет статус ptz.

        """
        # ----------------------------------------
        # ПРОВЕРКА ВХОДНЫХ ДАННЫХ
        key_names = ['template_path', 'period', 'iterations']
        tools.check_keys_exist(self._input_data, key_names, 'data', True, self._statistic)
        key_values = [self._input_data["template_path"], self._input_data["period"], self._input_data["iterations"]]
        tools.check_types(key_names, key_values, [str, int, int], self._statistic)
        # ----------------------------------------

        ws_client = SoapClient(self._ip, self._port, self._config, self._statistic)
        token = ws_users.server_login(ws_client, self._login, self._password, self._statistic)

        if self._input_data["template_path"]:
            template_ptz_list_profiles: dict = tools.open_json_file(self._input_data["template_path"], self._statistic)
            template_ptz_list_profiles: list = template_ptz_list_profiles["result"]
            self._statistic.append_info("Получен шаблон из файла...", "ИНФО")
        else:
            template_ptz_list_profiles: list = ws_ptz.ptzserver_list_profiles(ws_client, token, self._statistic)
            if not template_ptz_list_profiles:
                self._statistic.append_error("Неуспешно... Список PTZ камер пуст!", "ПОЛУЧЕНИЕ ШАБЛОНА", True)
            self._statistic.append_info("Получен шаблон из ws ptzserver:list_profiles...", "ИНФО")

        if not template_ptz_list_profiles:
            self._statistic.append_error("Пустой список камер в шаблоне!", "ВХ_ДАННЫЕ", True)

        for iteration in range(self._input_data["iterations"]):
            local_servers: dict = ws_lp.get_local_servers(ws_client, token, 1, self._statistic)
            if tools_lp.check_ptz_cams(local_servers["cams"], template_ptz_list_profiles, self._statistic):
                self._statistic.append_success("Статусы PTZ в ответе ws listener_pinger:get_local_servers корректны!",
                                               "ТЕСТ")
            else:
                self._statistic.append_error("Статусы PTZ в ответе ws listener_pinger:get_local_servers некорректны!",
                                             "КРИТ", True)

            down_servers: dict = ws_lp.get_down_servers(ws_client, token, 1, self._statistic)
            if tools_lp.check_ptz_cams(down_servers["cams"], template_ptz_list_profiles, self._statistic):
                self._statistic.append_success("Статусы PTZ в ответе ws listener_pinger:get_down_servers корректны!",
                                               "ТЕСТ")
            else:
                self._statistic.append_error("Статусы PTZ в ответе ws listener_pinger:get_down_servers некорректны!",
                                             "КРИТ", True)

            time.sleep(self._input_data["period"])
