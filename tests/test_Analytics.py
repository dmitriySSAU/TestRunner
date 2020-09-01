import time
import random
from typing import Tuple

from lib.client.zmqClient import ZmqClient
from lib.client.soapClient import SoapClient
from lib.log_and_statistic.statistic import Statistic

from scripts.xml import zmq
from scripts.common import graph, tools
from scripts.tools import analytics

from scripts.ws import users as ws_users
from scripts.ws import common as ws_common
from scripts.ws import ewriter as ws_ewriter
from scripts.ws import faceva as ws_analytics


class TestAnalytics:
    """Класс-обертка с тестами по аналитике

    """
    def __init__(self, input_data: dict, config: dict, statistic: Statistic):
        self._statistic: Statistic = statistic
        self._logger = self._statistic.get_log().get_logger("test/test_Analytics")

        self._input_data: dict = input_data
        self._config: dict = config

        self._server_ip: str = config['server']['ip']
        self._server_port: int = config['server']['ws_port']
        self._login: str = config['user']['login']
        self._password: str = config['user']['password']
        self._server_db_path: str = config['server']['db_path']

    def setup(self):
        """Данный метод вызывается перед запуском каждого теста.

        """
        pass

    def teardown(self):
        """Данный метод вызывается по завершению каждого теста.

        """
        pass

    def test_faceva_get_event(self):
        """Тест проверяет ws метод FaceVA:GetEvent.
        Тест может работать в двух режимах: skd_mode = True - используются только ws методы лиц, то есть точно также,
        как и вызвает их СКД; skd_mode = False - за эталон берутся события системы и сравниваются с событиями от лиц,
        таким образом проверяются возможные пропуски.

        max_counts_event - кол-во событий для проверки, при достижении которых тест должен завершиться.
        event_getting_timeout - как часто запрашивать события, в случае если они не были найдены.

        """
        ws_client = SoapClient(self._server_ip, self._server_port, self._config, self._statistic)
        token: str = ws_users.server_login(ws_client, self._login, self._password, self._statistic)
        current_time = ws_common.get_current_server_time(ws_client, token, self._statistic)

        events_count = 0
        last_event_time = current_time
        last_event_id = 0
        from_event = 0
        while True:
            if self._input_data['skd_mode']:
                events: Tuple[dict] = ws_analytics.faceva_get_event(ws_client, token, from_event, self._statistic)
            else:
                events: Tuple[dict] = ws_ewriter.select(ws_client, token, last_event_time, None, None, [20013], None,
                                                        None, None, self._statistic)
                events: list = list(events)
                events.reverse()

            if not events or len(events) == 1 and events[0] == {}:
                time.sleep(self._input_data['event_getting_timeout'])
                continue
            events: tuple = tuple(events)
            self._statistic.append_info("Получены события", "ИНФО")

            for index, event in enumerate(events):
                events_count += 1
                if self._input_data['skd_mode'] is False:
                    # пропускаем старые (уже проверенные) события
                    if event['evtid'] <= last_event_id:
                        events_count -= 1
                        continue

                    faceva_events: Tuple[dict] = ws_analytics.faceva_get_event(ws_client, token, 0, self._statistic)
                    index_faceva_event = tools.get_dict_by_keys_values(faceva_events, ('event', ), (event['evtid'], ))

                    if index_faceva_event < 0:
                        self._statistic.append_error("Нет события: " + str(event['evtid']) + "!", "КРИТ", True)

                    person_id = faceva_events[index_faceva_event]['person']
                    persons = ws_analytics.faceva_get_data_base(ws_client, token, self._statistic)
                    index_person = tools.get_dict_by_keys_values(persons, ('id', ), (person_id, ))

                    if index_person < 0:
                        self._statistic.append_error("В базе нет id: " + str(person_id) + "!", "КРИТ", True)

                    person_name = persons[index_person]['name']

                    if event['evtcomment'].find(person_name) < 0:
                        self._statistic.append_error("ФИО персоны не совпадают в событии " + str(event['evtid']) + "!",
                                                     "НЕВАЛИД ЗНАЧ", False)

                    event_id = faceva_events[index_faceva_event]['event']
                    time_ = faceva_events[index_faceva_event]['time']
                    camera = faceva_events[index_faceva_event]['camera']

                    event_time: str = event['evttime']
                    date_event_time = tools.get_date_from_str(event_time)
                    last_event_time = str(tools.convert_time_to_gtc(date_event_time))[:-3]
                    last_event_id = event_id
                else:
                    event_id = event['event']
                    time_ = event['time']
                    camera = event['camera']
                    from_event = event_id

                # Проверка получения кадра по событию.
                # Выполнение ws метода FaceVA:GetFrame
                ws_result = ws_analytics.faceva_get_frame(ws_client, token, camera, time_, self._statistic)
                if tools.check_keys_exist(ws_result, ['img'], 'result[0]', False, self._statistic) is False:
                    self._statistic.append_error("По событию " + str(event_id) + "!", "ОТСУТСТВУЕТ КАДР", True)
                elif not ws_result['img']:
                    self._statistic.append_error("По событию " + str(event_id) + "!", "ОТСУТСТВУЕТ КАДР", True)
                else:
                    self._statistic.append_success("По событию '" + str(event_id) + "'!", "ПОЛУЧЕН КАДР")

                # Проверка получения картинки по событию.
                # Выполнение ws метода FaceVA:GetEventImage
                ws_result = ws_analytics.faceva_get_event_image(ws_client, token, event_id, time_, self._statistic)
                if tools.check_keys_exist(ws_result, ['img'], 'result[0]', False, self._statistic) is False:
                    self._statistic.append_error("По событию " + str(event_id) + "!", "ОТСУТСТВУЕТ КАРТИНКА", True)
                elif not ws_result['img']:
                    self._statistic.append_error("По событию " + str(event_id) + "!", "ОТСУТСТВУЕТ КАРТИНКА", True)
                else:
                    self._statistic.append_success("По событию " + str(event_id) + "!", "ПОЛУЧЕНА КАРТИНКА")

                if events_count >= self._input_data['max_count_events']:
                    break
            if events_count >= self._input_data['max_count_events']:
                break

    def test_faceva_get_faces(self):
        """Тест проверяет ws метод FaceVA:GetFaces.
        Тест может работать в двух режимах: skd_mode = True - используются только ws методы лиц, то есть точно также,
        как и вызвает их СКД; skd_mode = False - за эталон берутся события системы и сравниваются с событиями от лиц,
        таким образом проверяются возможные пропуски.

        max_counts_event - кол-во событий для проверки, при достижении которых тест должен завершиться.
        event_getting_timeout - как часто запрашивать события, в случае если они не были найдены.

        """
        ws_client = SoapClient(self._server_ip, self._server_port, self._config, self._statistic)
        token: str = ws_users.server_login(ws_client, self._login, self._password, self._statistic)
        current_time = ws_common.get_current_server_time(ws_client, token, self._statistic)

        events_count = 0
        last_event_time = current_time
        last_event_id = 0
        from_event = 0
        while True:
            if events_count >= self._input_data['max_count_events']:
                break
            if self._input_data['skd_mode']:
                events: Tuple[dict] = ws_analytics.faceva_get_faces(ws_client, token, from_event, self._statistic)
            else:
                events: Tuple[dict] = ws_ewriter.select(ws_client, token, last_event_time, None, None, [20072],
                                                        self._statistic)
                events: list = list(events)
                events.reverse()

            if not events or len(events) == 1 and events[0] == {}:
                time.sleep(self._input_data['event_getting_timeout'])
                continue

            self._statistic.append_info("Получены события", "ИНФО")

            for index, event in enumerate(events):
                if events_count >= self._input_data['max_count_events']:
                    break
                events_count += 1
                if self._input_data['skd_mode'] is False:
                    if event['evtid'] <= last_event_id:
                        events_count -= 1
                        continue

                    faceva_events: Tuple[dict] = ws_analytics.faceva_get_faces(ws_client, token, last_event_id,
                                                                               self._statistic)
                    index_faceva_event = tools.get_dict_by_keys_values(faceva_events, ['event'], [event['evtid']])

                    if index_faceva_event < 0:
                        self._statistic.append_error("Нет события: '" + str(event['evtid']) + "'", "КРИТ", True)

                    event_id = faceva_events[index_faceva_event]['event']
                    time_ = faceva_events[index_faceva_event]['time']
                    camera = faceva_events[index_faceva_event]['camera']
                    img = faceva_events[index_faceva_event]['img']

                    event_time: str = event['evttime']
                    date_event_time = tools.get_date_from_str(event_time, stat)
                    last_event_time = str(tools.convert_time_to_gtc(date_event_time))[:-3]
                    last_event_id = event_id
                else:
                    event_id = event['event']
                    time_ = event['time']
                    camera = event['camera']
                    img = event['img']
                    from_event = event_id

                # Проверка получения кадра по событию.
                # Выполнение ws метода FaceVA:GetFrame
                ws_result = ws_analytics.faceva_get_frame(ws_client, token, camera, time_, self._statistic)
                if tools.check_keys_exist(ws_result, ['img'], 'result[0]', False, self._statistic) is False:
                    self._statistic.append_error("По событию '" + str(event_id) + "'!", "ОТСУТСТВУЕТ_КАДР", True)
                elif not ws_result['img']:
                    self._statistic.append_error("По событию '" + str(event_id) + "'!", "ОТСУТСТВУЕТ_КАДР", True)
                else:
                    self._statistic.append_success("По событию '" + str(event_id) + "'!", "ПОЛУЧЕН_КАДР")

                # Проверка получения картинки по событию.
                if not img:
                    self._statistic.append_error("По событию '" + str(event_id) + "'!", "ОТСУТСТВУЕТ_КАРТИНКА", True)
                else:
                    self._statistic.append_success("По событию '" + str(event_id) + "'!", "ПОЛУЧЕНА_КАРТИНКА")

    def test_faceva_update_person(self):
        """Тест проверяет работу ws метода FaceVA:UpdatePerson.

            Тест добавляет с помощью этого ws метода персон из указанной директории, в которой находятся папки,
            имена которых являются ФИО персоны, а внутри каждой папки фотографии этой персоны. После каждого добавления
            вызывается метода FaceVA:GetDataBase с целью фактической проверки добавления человека.
        """
        ws_client = SoapClient(self._server_ip, self._server_port, self._config, self._statistic)
        token = ws_users.server_login(ws_client, self._login, self._password, self._statistic)

        # получение текущего списка людей в БД
        old_persons_db = ws_analytics.faceva_get_data_base(ws_client, self._login, self._statistic)
        persons_dir = tools.get_dirs(self._input_data["persons_dir"])

        for person in persons_dir:
            name: str = person
            category: str = str(random.randint(0, 100000))
            comment: str = random.choice(["На больничном", "Удаленная работа", "Полная ставка", "Пол ставки", "Фрилансер"])
            information: str = random.choice(["Программист", "Тестировщик", "Директор", "Начальник отдела тестирования",
                                              "Менеджер по продажам"])
            department: str = random.choice(["Тестирования", "Разработки ПО", "Продаж", "Кадров"])
            person_photos: Tuple[str] = tools.get_files(self._input_data["persons_dir"] + "/" + person)
            photo_paths = []
            for person_photo in person_photos:
                photo_paths.append(self._input_data["persons_dir"] + "/" + person + "/" + person_photo)
            photos_base64: Tuple[str] = tools.get_photos_base64(tuple(photo_paths))
            faces = []
            for photo_base64 in photos_base64:
                faces.append({
                    "img": str(photo_base64)
                })
            while True:
                pacs_id: int = random.randint(0, 1000)
                if tools.get_dict_by_keys_values(old_persons_db, ("pacs", ), (pacs_id, )) == -1:
                    break

            person_id = ws_analytics.faceva_update_person(ws_client, token, -1, pacs_id, name, category, comment,
                                                          information, department, faces, [], self._statistic)
            current_persons_db = ws_analytics.faceva_get_data_base(ws_client, token, self._statistic)

            key_names = ("id", "name", "pacs", "category", "comment", "information", "department")
            key_values = (person_id, name, pacs_id, category, comment, information, department)
            if tools.get_dict_by_keys_values(current_persons_db, key_names, key_values) == -1:
                self._statistic.append_error(name, "ПЕРСОНА НЕ ДОБАВЛЕНА", True)

            self._statistic.append_success(name, "ПЕРСОНА ДОБАВЛЕНА")
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

    def test_analytic_events(self):
        """Тест строит указанное кол-во графов устройство->микшер->ИВ54сервер->аналитика,
            затем ожидает конца дампа/ави и сравнивает фактичиские события с указанными в data
        """
        analytic_block: dict = tools.open_json_file(self._input_data['json'], self._statistic)
        cam_json = graph.create_json_from_profiles(self._input_data['server'], analytic_block,
                                                   self._input_data['video_source'], True, self._statistic)
        ws_client = SoapClient(self._server_ip, self._server_port, self._config, self._statistic)
        token: str = ws_users.server_login(ws_client, self._login, self._password, self._statistic)
        cam_name: str = graph.insert_graphs_to_db(ws_client, token, self._server_db_path, cam_json,
                                                  self._input_data['server'], self._input_data['profile'], 1,
                                                  self._statistic)[0]
        if self._input_data['detector'] == "forget2":
            event_type = 20074
        elif self._input_data['detector'] == "FaceVA":
            event_type = 20013
        else:
            self._statistic.append_error(self._input_data['detector'], "НЕТ ДЕТЕКТОРА", True)
        cam_info = {
            "server": self._input_data['server'],
            "cam": cam_name,
            "profile": self._input_data['profile']
        }
        analytics.run_events_test(ws_client, token, cam_info, self._input_data['events'],
                                  self._input_data['inaccuracy'], event_type, self._input_data['video_source'],
                                  self._statistic)

    def simple_kars(self):
        """Тест проверяет работу модуля лиц по протоколу zmq.

        """
        zmqclient = ZmqClient(self._config, self._statistic)
        zmqclient.start_handler_thread()
        timeout = 2.0
        # отправка hello
        message_id = zmq.send_hello(zmqclient, 1212, timeout, self._statistic)

        # отправка enroll_models
        model_data = zmq.send_enroll_models(zmqclient, self._input_data["path_to_photo"], timeout, self._statistic)
        descriptor = model_data[0]
        model_id = model_data[1]

        # отправка AddModelToHotlist
        zmq.send_add_model_to_hot_list(zmqclient, model_id, descriptor, 1, 0, 1, timeout, self._statistic)

        # TODO логика ожидания
        while True:
            time.sleep(10)


        zmqclient.stop_handler_thread()
