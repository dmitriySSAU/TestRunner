import re

import time
import json
import random

from scripts.tools import common
from scripts.common import tools
from scripts.ws import users as ws_users
from scripts.ws import common as ws_common

from lib.client.soapClient import SoapClient

from lib.log_and_statistic import log
from lib.log_and_statistic.statistic import Statistic


class TestCommon:

    def __init__(self, input_data: dict, config: dict, statistic: Statistic):
        #self._logger = log.get_logger("test/test_Common")

        self._statistic: Statistic = statistic
        self._input_data: dict = input_data
        self._config: dict = config

        self._server_ip: str = config['server']['ip']
        self._server_port: int = config['server']['ws_port']

        self._client_ip: str = config['client_QML']['ip']
        self._client_port: int = config['client_QML']['port']

        self._login: str = config['user']['login']
        self._password: str = config['user']['password']

    def setup(self):
        """
            setup function runs before every test method
        """
        pass

    def teardown(self):
        """
            teardown function runs after every test method
        """
        pass

    def directories_comparator(self) -> None:
        """Сравнение двух директорий
        Два файла равны, если их имена и содержимое одинаковы.
       """

        dir1 = self._input_data['first_path']
        dir2 = self._input_data['second_path']

        common.compare_dirs(dir1, dir2, self._statistic)

    def check_plugins_versions(self) -> None:
        """ Проверка версий плагинов
        Проверка версий плагинов из списка
        Обращение к WS с запросом версии плагина с помощью метода ws plugin_info:GetInfo

        Возможно два режима проверки: server и client.
        Режим server - проверка версии плагинов на сервере
        Режим client - проверка версии плагинов на клиенте
        """
        # ----------------------------------------
        # ПРОВЕРКА ВХОДНЫХ ДАННЫХ

        tools.check_keys_exist(self._input_data, ["plugins"], 'input_data', True, self._statistic)
        tools.check_types(["plugins"], [self._input_data["plugins"]], [list], self._statistic)
        tools.check_values(["len(plugins)"], [len(self._input_data["plugins"])], [0], ["!="], self._statistic)

        tools.check_keys_exist(self._input_data, ["mode"], 'input_data', True, self._statistic)
        tools.check_types(["mode"], [self._input_data["mode"]], [str], self._statistic)
        tools.check_values(["mode"], [self._input_data["mode"]], [""], ["!="], self._statistic)

        key_names = ['module_name', 'rel_path']
        for plugin in self._input_data["plugins"]:
            tools.check_keys_exist(plugin, key_names, "plugin", True, self._statistic)
            tools.check_types(key_names, [plugin[key_names[0]], plugin[key_names[1]]], [str, str], self._statistic)
            tools.check_values(key_names, [plugin[key_names[0]], plugin[key_names[1]]], ["", ""], ["!=", "!="],
                               self._statistic)
        # ----------------------------------------

        if self._input_data["mode"] == "server":
            ws_client = SoapClient(self._server_ip, self._server_port, self._config, self._statistic)
        elif self._input_data["mode"] == "client":
            ws_client = SoapClient(self._client_ip, self._client_port, self._config, self._statistic)
        else:
            self._statistic.append_error("Недопустимое значение ключа 'mode'. Доступны: client, server",
                                         "ОШИБКА КЛЮЧА JSON", True)

        token = ws_users.server_login(ws_client, self._login, self._password, self._statistic)

        for plugin in self._input_data["plugins"]:
            result: dict = ws_common.get_plugin_info(ws_client, token, plugin['rel_path'], plugin['module_name'],
                                                     self._statistic)
            if result['version'] == "not found module version !":
                self._statistic.append_error(plugin['module_name'], "ОШИБКА ВЕРСИИ МОДУЛЯ")
            if plugin['rel_path'] == "bad rel_path !":
                self._statistic.append_warn("Модуль " + plugin['module_name'] + " " + plugin['rel_path'],
                                            "НЕКОРРЕКТНЫЙ ПУТЬ")

            module_info: str = "Version: " + result['version'] + "\n" + "User: " + result['user'] + "\n" + "Build: " + \
                               result['build'] + "\n"
            self._statistic.append_success(
                "Имя модуля: " + plugin['module_name'] + "\n" + "Путь: " + plugin['rel_path'] + "\n" + module_info,
                "МОДУЛЬ ИНФО")

    def set_random_time_to_json(self) -> None:
        """
        Втавка в указанный json файл рандомизрованного значения по указанному ключу.
        Значение поля генерируется с учетом ограничения на дату (интервал дат указывается во входный данных теста)

        :return:
        """
        # fpattern = r'[0-9]{4}.(0[1-9]|1[012]).(0[1-9]|1[0-9]|2[0-9]|3[01])[-]{1}([0-1]\d|2[0-3])(:[0-5]\d){2}'
        # spattern = r'[0-9]{4}.(0[1-9]|1[012]).(0[1-9]|1[0-9]|2[0-9]|3[01])[ ]{1}([0-1]\d|2[0-3])(:[0-5]\d){2}'

        formats_array = ["%Y.%m.%d-%H:%M:%S", "%Y.%m.%d %H:%M:%S"]

        path = self._input_data["json_path"]
        cams_dict: dict = tools.open_json_file(path, self._statistic)  # открываем json по указанному пути и получаем словарь
        tools.check_keys_exist(cams_dict, ["cams"], "cams_dict", True, self._statistic)
        for cam in cams_dict["cams"]:
            tools.check_keys_exist(cam, ["archive"], "archive", False, self._statistic)

        for format_str in formats_array:
            try:
                if time.strptime(self._input_data["start_date"], format_str):
                    output_format: str = format_str
            except ValueError:
                continue

        sdate = time.mktime(time.strptime(self._input_data["start_date"], output_format))  # преобразуем входную дату в struct_time, а затем переводим все в секунды
        edate = time.mktime(time.strptime(self._input_data["end_date"],  output_format))  # преобразуем входную дату в struct_time, а затем переводим все в секунды

        # if re.match(fpattern, self._input_data["start_date"]) and re.match(fpattern, self._input_data["end_date"]):
        #     separator: str = "-"
        # if re.match(spattern, self._input_data["start_date"]) and re.match(spattern, self._input_data["end_date"]):
        #     separator: str = " "
        # format_str: str = '%Y.%m.%d' + separator + '%H:%M:%S'
        # sdate = time.mktime(time.strptime(self._input_data["start_date"], format_str))  # преобразуем входную дату в struct_time, а затем переводим все в секунды
        # edate = time.mktime(time.strptime(self._input_data["end_date"],  format_str))  # преобразуем входную дату в struct_time, а затем переводим все в секунды

        delta: float = edate - sdate  # разница в секундах между начальной и конечной датой

        for cam in cams_dict["cams"]:
            rand: float = random.random()  # случайное число [0;1]
            ndate: float = sdate + delta * rand  # генерируем новую дату
            # new_date: str = time.strftime('%Y.%m.%d-%H:%M:%S', time.localtime(ndate))  # перевод в строковый формат
            new_date: str = time.strftime(output_format, time.localtime(ndate))  # перевод в строковый формат
            cam["archive"] = new_date

        with open(path, 'w', encoding='utf-8') as json_file:
            json.dump(cams_dict, json_file, ensure_ascii=False, indent="\t")

