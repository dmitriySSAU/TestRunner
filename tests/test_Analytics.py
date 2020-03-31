import time
import random
import threading
import configparser
from typing import List

from lib.runner import initializer
from lib.log_and_statistic import log
from lib.client.zmqClient import ZmqClient
from lib.client.soapClient import SoapClient
from lib.log_and_statistic.statistics import Statistic

from scripts.xml import zmq
from scripts.common import graph, tools

from scripts.ws import users as ws_users
from scripts.ws import ewriter as ws_ewriter
from scripts.ws import analytics as ws_analytics

from requests_patterns.web import profiles


class TestAnalytics:
    """Класс-обертка с тестами по аналитике

    """
    def __init__(self):
        self._statistic = Statistic()
        self._full_json = {}
        self._logger = log.get_logger("test\\test_Analytics")

        config = configparser.ConfigParser()
        config.read(log.path + "\\runner.conf")
        self._ip = config.get("server", "ip")
        self._port = config.get("server", "port")
        self._login = config.get("user", "login")
        self._password = config.get("user", "password")
        self._current_test = ""

    def get_statisitc(self) -> Statistic:
        """Метод-геттер объекта статисики.

        Используется для получения объекта из другого потока (AnalyticThread)
        :return: объект класса Statistic
        """
        return self._statistic

    def get_tests_methods(self) -> dict:
        """Получение указателей на методы тестов по их имени

        :return: словарь указателей
        """
        return {
            "test_facesdbeditor_update_person": self.test_facesdbeditor_update_person
        }

    def setup(self):
        """Данный метод вызывается перед запуском каждого теста.

        """
        self._full_json = tools.open_json_file(log.path + '\\tests\\data\\Analytics.json', self._statistic)

    def teardown(self):
        """Данный метод вызывается по завершению каждого теста.

        """
        print("----------------------------------FINISH------------------------------------\n")

        self._logger.info("show error statistic")

        self._statistic.show_common_statistic()
        self._statistic.show_errors_statistic()
        self._statistic.show_warns_statistic()
        time.sleep(0.1)

    class AnalyticThread(threading.Thread):
        """Данный класс реализует функционал многопоточности.

           Позволяет одновременно тестировать одну и ту же аналитику на нескольких камерах (видео).
        """

        def __init__(self, id_, params, test_analytics, thread_common_lock, logger):
            threading.Thread.__init__(self)
            self._id = id_
            self._logger = logger
            self._test_analytics = test_analytics
            self._statistic = self._test_analytics.get_statisitc()
            self._current_test_params = params
            self._wait_lock = threading.Lock()
            self._wait_lock.acquire()
            self._event_change_lock = threading.Lock()
            self._event = {}

        def get_wait_lock(self):
            return self._wait_lock

        def get_event(self):
            return self._event

        def get_event_change_lock(self):
            return self._event_change_lock

        def run(self):
            # описание элементов current_test_params
            # 0 - путь к db
            # 1 - key1
            # 2 - словарь json элемента массива cam из data json

            self._logger.info("start thread")

            tools.check_types(['events'], [self._current_test_params[2]['events']], [list], self._statistic)
            tools.check_values(['events'], [self._current_test_params[2]['events']], [0], [">"], self._statistic)

            file_type = tools.get_file_type(self._current_test_params[2]['video_source'])

            # в зависимоти от типа файла строится нужный граф
            # либо устройство мультимедиа для медиа-файлов либо устройство ip камеры для дампов
            if file_type == "raw":
                data_dump: tuple = tools.get_dump_name_and_step(self._current_test_params[2]['video_source'])
                device: dict = profiles.get_ipcameras_dict("ipcameras:RVI:Unknown", "1", "admin", "admin", data_dump[0],
                                                           data_dump[1])
            else:
                device: dict = profiles.get_device_media_dict(self._current_test_params[2]['video_source'])

            common: dict = profiles.get_common_dict(self._current_test_params[1], "1")
            muxer: dict = profiles.get_muxer_dict("trackSource")
            iv54server: dict = profiles.get_network_5_4_dict(1)
            dicts: list = [common, device, muxer, iv54server]
            # вставка графа в бд
            client: SoapClient = SoapClient(self._test_analytics.ip, self._test_analytics.port, self._statistic)
            cam_key2: str = graph.insert_graphs_to_db(client, self._test_analytics.login, self._test_analytics.password,
                                                      self._current_test_params[0], tools.get_full_dict(dicts),
                                                      self._current_test_params[1], self._current_test_params[2]['key3'],
                                                      1, self._statistic)[0]

            token = ws_users.login(client, self._test_analytics.login, self._test_analytics.password)
            # цикл ожидания - ждем, пока отсутствуют кадры по данному источнику видео
            while True:
                if file_type == "raw":
                    ipcam_stat = tools.get_statistic_by_cam(client, self._current_test_params[1], cam_key2,
                                                            self._statistic)
                    if ipcam_stat == {}:
                        time.sleep(1)
                        continue
                    if ipcam_stat['FPSVideo'] == 0:
                        time.sleep(0.1)
                        continue
                    start_time = ipcam_stat['TimeLastVideo']
                    break
                # else:
                # Тут должен быть код запроса статистики по авишки

            # получаем максимальное значение ключа finish
            # данное значение является максимальным временем ожидания
            # после которого считаем, что видео завершено и можно проверять события
            max_finish_val = tools.get_max_value_by_key(self._current_test_params[2]['events'], "finish",
                                                        self._statistic)
            # вычисление задержки для sleep для прогресса в 1%
            sleep_1_persent = max_finish_val / 100
            current_progress = 0
            # ожидание завершения видео
            while True:
                time.sleep(sleep_1_persent)
                current_progress += 1
                if current_progress == 100:
                    log.print_test("Камера '" + cam_key2 + "' полностью проиграна!")
                    break
                log.print_all("Прогресс камеры '" + cam_key2 + "': " + str(current_progress) + "%")
            start_time = tools.get_date_from_str(start_time)
            for event in self._current_test_params[2]['events']:
                tools.check_keys_exist(event, ['begin', 'finish', 'count_events'], 'events', True, self._statistic)

                begin_time = tools.increment_time(start_time, event['begin'])
                finish_time = tools.increment_time(start_time, event['finish'])

                begin_time_gtc = tools.convert_time_to_gtc(begin_time)
                finish_time_gtc = tools.convert_time_to_gtc(finish_time)

                ws_ewriter.select(client, token, str(begin_time_gtc), str(finish_time_gtc),
                                  self._current_test_params.login, [])
                # далее должна быть логика по проверки события

    def test_faceva_events(self):
        """Сравнение фактических событий с эталоном по видео для детектора лиц.

           Тест построит полный граф с указанным дампом, добавит детектор FaceVA
           и сравнит реальные сработки с указанными в data
        """
        self._current_test = "test_faceva_events"
        self._logger.info("START TEST " + self._current_test)

        data = initializer.init_data(self._full_json, self._current_test, self._statistic)

        list_run_threads = []
        thread_common_lock = threading.Lock()
        for index, cam in enumerate(data['cams']):
            params_for_thread = []
            thread = self.AnalyticThread((index + 1), params_for_thread, self, thread_common_lock, self._logger)
            thread.start()
            list_run_threads.append(thread)
            #if len(list_run_threads) < data['cams_at_the_same_time']:
            #    continue

    def test_facesdbeditor_update_person(self):
        """Тест проверяет работу ws метода FaceVA:UpdatePerson.

            Тест добавляет с помощью этого ws метода персон из указанной директории, в которой находятся папки,
            имена которых являются ФИО персоны, а внутри каждой папки фотографии этой персоны. После каждого добавления
            вызывается метода FaceVA:GetDataBase с целью фактической проверки добавления человека.
        """
        self._current_test = "test_facesdbeditor_update_person"
        self._logger.info("START TEST " + self._current_test)

        input_data = initializer.init_data(self._full_json, self._current_test, self._statistic)

        key_names: list = ['persons_dir']
        tools.check_keys_exist(input_data, key_names, 'data', True, self._statistic)

        key_values: list = [input_data["persons_dir"]]
        key_types: list = [str]
        tools.check_types(key_names, key_values, key_types, self._statistic)
        tools.check_values(key_names, key_values, [""], ["!="], self._statistic)

        client = SoapClient(self._ip, self._port, self._statistic)

        old_persons_db = ws_analytics.faceva_get_data_base(client, self._login, self._password, self._statistic)  # получение текущего списка людей в БД
        persons_dir = tools.get_dirs(input_data["persons_dir"])

        for person in persons_dir:
            name: str = person
            category: str = str(random.randint(0, 100000))
            comment: str = random.choice(["На больничном", "Удаленная работа", "Полная ставка", "Пол ставки", "Фрилансер"])
            information: str = random.choice(["Программист", "Тестировщик", "Директор", "Начальник отдела тестирования",
                                              "Менеджер по продажам"])
            department: str = random.choice(["Тестирования", "Разработки ПО", "Продаж", "Кадров"])
            person_photos: List[str] = tools.get_files(input_data["persons_dir"] + "\\" + person)
            photo_paths: List[str] = []
            for person_photo in person_photos:
                photo_paths.append(input_data["persons_dir"] + "\\" + person + "\\" + person_photo)
            photos_base64: List[str] = tools.get_photos_base64(photo_paths)
            faces: List[dict] = []
            for photo_base64 in photos_base64:
                faces.append({
                    "img": str(photo_base64)
                })
            while True:
                pacs_id: int = random.randint(0, 1000)
                if tools.get_dict_by_keys_values(old_persons_db, ["pacs"], [pacs_id]) == -1:
                    break

            person_id = ws_analytics.faceva_update_person(client, self._login, self._password, -1, pacs_id, name, category,
                                                          comment, information, department, faces, [], self._statistic)

            current_persons_db = ws_analytics.faceva_get_data_base(client, self._login, self._password, self._statistic)  # получение текущего списка людей в БД

            key_names = ["id", "name", "pacs", "category", "comment", "information", "department"]
            key_values = [person_id, name, pacs_id, category, comment, information, department]
            if tools.get_dict_by_keys_values(current_persons_db, key_names, key_values) == -1:
                self._statistic.append_error("'" + name + "'", "ОШИБКА_ДОБАВЛЕНИЯ", True)

            log.print_test("Персона '" + name + "' успешно добавлена!")
            """# запуск удаления
            for person_name in current_new_persons:
                # удаление из базы
                analytics.faceva_delete_person(client, self.login, self.password, person_name)
                # получение текущего списка людей в БД
                persons_db = analytics.faceva_get_data_base(client, self.login, self.password)
                # если после удаления человек в базе остался, то произошла ошибка удаления
                if tools.get_dict_by_keys_values(persons_db, ["name"], [person_name]) != -1:
                    log.print_error("delete person '" + person_name + "' has done with error! It exists in data base"
                                                                      " after delete")
                    continue
                log.print_test("delete person '" + person_name + "' was executed successfully!")
            # очистка списка новых людей, которые были удалены
            current_new_persons.clear() """

    def test_forget_events(self):
        """Тест строит указанное кол-во графов устройство->микшер->ИВ54сервер->аналитика,
            затем ожидает конца дампа/ави и сравнивает фактичиские события с указанными в data
        """
        self._current_test = "test_forget_events"
        self._logger.info("START TEST " + self._current_test)

        input_data = initializer.init_data(self._full_json, self._current_test, self._statistic)

        tools.check_keys_exist(input_data, ['path_to_db', 'key1', 'cams_at_the_same_time', 'cams'], 'data', True,
                               self._statistic)

        # TODO многопоточная логика теста

    def test_kars_zmq(self):
        """Тест проверяет работу модуля лиц по протоколу zmq.

        """
        self._current_test = "test_kars_zmq"
        self._logger.info("START TEST " + self._current_test)

        input_data = initializer.init_data(self._full_json, self._current_test, self._statistic)

        zmqclient = ZmqClient()
        zmqclient.start_handler_thread()
        timeout = 2.0
        # отправка hello
        message_id = zmq.send_hello(zmqclient, 1212, timeout, self._statistic)

        # отправка enroll_models
        model_data = zmq.send_enroll_models(zmqclient, input_data["path_to_photo"], timeout, self._statistic)
        descriptor = model_data[0]
        model_id = model_data[1]

        # отправка AddModelToHotlist
        zmq.send_add_model_to_hot_list(zmqclient, model_id, descriptor, 1, 0, 1, timeout, self._statistic)

        # TODO логика ожидания
        while True:
            time.sleep(10)


        zmqclient.stop_handler_thread()

    # TODO def test_faceva_with_skd(self):
