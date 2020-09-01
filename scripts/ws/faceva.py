from typing import Tuple

from scripts.common import tools

from requests_patterns.ws import faceva as pattern

from lib.log_and_statistic import log
from lib.log_and_statistic.statistic import Statistic

from lib.client.soapClient import SoapClient


def faceva_get_data_base(client: SoapClient, token: str, statistic: Statistic) -> tuple:
    """Функция выполнеия ws метода FaceVA:GetDataBase

    :param client: объект класса SoapClient для отправки и приема ws запросов;
    :param token: токен соединения;
    :param statistic: объект класса Statistic для ведения статистики ошибок и предупреждений.

    :return: список персон, который приходит в ответе в ключе persons вида:
        [
            {
                "id": 26617065162932227,
                "name": Иванов Иван Иванович,
                ["pacs": 1],
                ["category": "category"],
                ["department": "department"],
                ["comment": "comment"],
                ["information": "information"]
            }
        ]
    """
    logger = statistic.get_log().get_logger("scripts/ws/analytics")
    logger.info("was called(client, login, password)")
    logger.debug("with params (client_obj, " + token + ", stat_obj)")

    params, sysparams, method = pattern.faceva_get_data_base(token)
    response_json = client.call_method2(method, params, sysparams, [0])
    result = response_json["result"][0]

    tools.check_keys_exist(result, ['persons'], "result", True, statistic)
    persons = result["persons"]
    tools.check_types(["persons"], [persons], [list], statistic)

    if not persons:
        statistic.append_warn("data base persons", "EMPTY")

    for person in persons:
        tools.check_keys_exist(person, ["id", "name"], 'person', True, statistic)

    logger.info("ws method FaceVA:GetDataBase was executed successfully!")
    statistic.append_info(method + " выполнен успешно!", "WS МЕТОД")

    return tuple(persons)


def faceva_update_person(client: SoapClient, token: str, id_: int, pacs_id: int, name: str, category: str,
                         comment: str, information: str, department: str, faces: Tuple[dict], delete_faces: Tuple[dict],
                         statistic: Statistic) -> str:
    """Функция выполнения ws метода FaceVA:UpdatePerson.

    :param client: объект класса SoapClient для отправки и приема ws запросов;
    :param token: токен соединения;
    :param id_: идентификатор персоны в БД;
    :param pacs_id: идентификатор персоны в БД для СКД;
    :param name: ФИО персоны;
    :param category: категория;
    :param comment: комментарий;
    :param information: информация;
    :param department: отдел;
    :param faces: список фото лиц для добавления;
    :param delete_faces: список фото для удаления;
    :param statistic: объект класса Statistic для ведения статистики ошибок и предупреждений.

    :return: идентификатор персоны в базе.
    """
    logger = statistic.get_log().get_logger("scripts/ws/analytics")
    logger.info("was called faceva_update_person(client: SoapClient, login: str, id_: int, pacs_id: int,\
                name: str, category: str, comment: str, information: str, department: str, faces: List[dict], \
                delete_faces: List[dict])")
    logger.debug("faceva_update_person(client_obj" + token + ", " + str(id_) + ", " + str(pacs_id) +
                 ", " + name + ", " + category + ", " + comment + ", " + information + ", " + department + ", " +
                 ", " + str(faces) + ", " + str(delete_faces) + ")")

    params, sysparams, method = pattern.faceva_update_person(token, id_, pacs_id, name, category, comment, information,
                                                             department, faces, delete_faces)
    response_json = client.call_method2(method, params, sysparams, [0])

    person = response_json['result'][0]
    key_names = ["id", "pacs", "name", "category", "comment", "information", "department", "result", "faces"]
    tools.check_keys_exist(person, key_names, "['result'][0]", True, statistic)

    key_names.remove("result")
    key_names.remove("faces")
    key_values = [person["id"], person["pacs"], person["name"], person["category"], person["comment"],
                  person["information"], person["department"]]
    key_need_values = [id_, str(pacs_id), name, category, comment, information, department]
    operations = ["==", "==", "==", "==", "==", "==", "=="]
    if id_ == -1:
        key_names.pop(0)
        key_values.pop(0)
        key_need_values.pop(0)
        operations.pop(0)
    tools.check_values(key_names, key_values, key_need_values, operations, statistic)

    tools.check_types(["faces"], [person["faces"]], [list], statistic)

    if not person['faces'] and faces:
        statistic.append_error("Список faces", "НЕТ_ЛИЦ", True)

    for index, face in enumerate(person["faces"]):
        tools.check_keys_exist(face, ["result"], "face", True, statistic)
        if face["result"] == "error":
            tools.check_keys_exist(face, ["reason"], "face", True, statistic)
            statistic.append_error("причина: " + face["reason"], "ПЛОХОЕ_ФОТО", False)

    logger.info("ws method FaceVA:UpdatePerson was executed successfully!")
    statistic.append_info(method + " выполнен успешно!", "WS МЕТОД")

    return person["id"]


# TODO переделать под идентификатор
def faceva_delete_person(client: SoapClient, token: str, name: str, statistic: Statistic) -> bool:
    """Функция выполнения ws метода FaceVA:DeletePerson

    :param client: объект класса SoapClient для отправки и приема ws запросов;
    :param token: токен соединения;
    :param name:
    :param statistic:
    :return: флаг успешности операции
    """
    logger = log.get_logger("scripts/ws/analytics")
    logger.info("was called (client: SoapClient, login: str, password: str, name: str, statistic: Statistic)")
    logger.debug("faceva_delete_person(client_obj" + login + ", " + password + ", " + name + ")")

    data = pattern.faceva_delete_person(login, password, name)
    response_json = client.call_method2(data[2], data[0], data[1], True)
    logger.debug("response_json: " + str(response_json))

    tools.check_keys_exist(response_json['result'][0], ['cmd', 'name'], "response_json['result'][0]", True, statistic)
    #tools.check_on_equal_key_values_in_dict(response_json["result"][0], ['cmd', 'name'], ['DeletePerson', name])

    logger.info("ws method FaceVA:DeletePerson was executed successfully!")
    statistic.append_info(method + " выполнен успешно!", "WS МЕТОД")

    return True


def faceva_get_event(client: SoapClient, token: str, from_: int, statistic: Statistic) -> Tuple[dict]:
    """Функция выполнения ws метода FaceVA:GetEvent.

    :param client: объект класса SoapClient для отправки и приема ws запросов;
    :param token: токен соединения;
    :param from_: начиная с какого id прислать события
    :param statistic: объект класса Statistic для ведения статистики ошибок и предупреждений

    :return: список словарей с событиями вида:
        [
            {
                "event": 154743,
                "camera": 1955154395,
                "person": "26617065381036041",
                "score": 0.939386,
                "time": 1587380094085000,
                "rect": {
                    "x": 308,
                    "y": 364,
                    "w": 98,
                    "h": 98
                }
            },
            ...
            ...
        ]
    """
    logger = statistic.get_log().get_logger("scripts/ws/analytics")
    logger.info("was called (client: SoapClient, token: str, from_: int, statistic: Statistic)")
    logger.debug("params (client_obj" + token + ", " + str(from_) + ", stat_obf)")

    params, sysparams, method = pattern.faceva_get_event(token, from_)
    response = client.call_method2(method, params, sysparams, [0])

    for index, event in enumerate(response['result']):
        # пришлось написать это условие, так как может быть ситуация: result: [{}],
        # это означает, что событий нет.
        if not event and len(response['result']) == 1:
            break
        key_names = ['event', 'camera', 'person', 'score', 'time', 'rect']
        tools.check_keys_exist(event, key_names, "result[" + str(index) + "]", True, statistic)
        key_values = [event['event'], event['camera'], event['person'], event['score'], event['time'], event['rect']]
        tools.check_types(key_names, key_values, [int, int, str, float, int, dict], statistic)

        key_names = ['x', 'y', 'w', 'h']
        tools.check_keys_exist(event['rect'], key_names, "result[" + str(index) + "]['rect']", True, statistic)
        key_values = [event['rect']['x'], event['rect']['y'], event['rect']['w'], event['rect']['h']]
        tools.check_types(key_names, key_values, [int, int, int, int], statistic)

    statistic.append_info(method + " выполнен успешно!", "WS МЕТОД")

    return tuple(response['result'])


def faceva_get_faces(client: SoapClient, token: str, from_: int, statistic: Statistic) -> Tuple[dict]:
    """Функция выполнения ws метода FaceVA:GetFaces.

    :param client: объект класса SoapClient для отправки и приема ws запросов;
    :param token: токен соединения;
    :param from_: начиная с какого id прислать события
    :param statistic: объект класса Statistic для ведения статистики ошибок и предупреждений

    :return: список словарей с событиями вида:
        [
            {
                "event": 154743,
                "camera": 1955154395,
                "person": "26617065381036041", // если не пустой, значит это СВОЙ, иначе просто обнаруженное лицо.
                "score": 0.939386,
                "time": 1587380094085000,
                "img": "base64"
            },
            ...
            ...
        ]
    """
    logger = statistic.get_log().get_logger("scripts/ws/analytics")
    logger.info("was called (client: SoapClient, token: str, from_: int, statistic: Statistic)")
    logger.debug("params (client_obj" + token + ", " + str(from_) + ", stat_obf)")

    params, sysparams, method = pattern.faceva_get_faces(token, from_)
    response: dict = client.call_method2(method, params, sysparams, [0])

    for index, event in enumerate(response['result']):
        # пришлось написать это условие, так как может быть ситуация: result: [{}],
        # это означает, что событий нет.
        if not event and len(response['result']) == 1:
            break
        key_names = ['event', 'camera', 'rect', 'score', 'time', 'img']
        tools.check_keys_exist(event, key_names, "result[" + str(index) + "]", True, statistic)
        key_values = [event['event'], event['camera'], event['rect'], event['score'], event['time'], event['img']]
        tools.check_types(key_names, key_values, [int, int, dict, float, int, str], statistic)

        key_names = ['x', 'y', 'w', 'h']
        tools.check_keys_exist(event['rect'], key_names, "result[" + str(index) + "]['rect']", True, statistic)
        key_values = [event['rect']['x'], event['rect']['y'], event['rect']['w'], event['rect']['h']]
        tools.check_types(key_names, key_values, [int, int, int, int], statistic)

    statistic.append_info(method + " выполнен успешно!", "WS МЕТОД")

    return tuple(response['result'])


def faceva_get_event_image(client: SoapClient, token: str, event: int, time: int, statistic: Statistic) -> dict:
    """Функция выполнения ws метода FaceVA:GetEventImage.

    :param client: объект класса SoapClient для отправки и приема ws запросов;
    :param token: токен соединения;
    :param event: номер события;
    :param time: время события (в unix формате);
    :param statistic: объект класса Statistic для ведения статистики ошибок и предупреждений

    :return: в случае успеха словарь ответа вида:
        {
            "img": "base64 code"
        }
        в случае ошибки словарь вида:
        {
            "result": "error"
        }
    """
    logger = statistic.get_log().get_logger("scripts/ws/analytics")
    logger.info("was called (client: SoapClient, token: str, event: int, time: int, statistic: Statistic)")
    logger.debug("params (client_obj" + token + ", " + str(event) + ", " + str(time) + ", stat_obf)")

    params, sysparams, method = pattern.faceva_get_event_image(token, event, time)
    response = client.call_method2(method, params, sysparams, [0])

    statistic.append_info(method + " выполнен успешно!", "WS МЕТОД")

    return response['result'][0]


def faceva_get_frame(client: SoapClient, token: str, camera: int, time: int, statistic: Statistic) -> dict:
    """Функция выполнения ws метода FaceVA:GetFrame.

    :param client: объект класса SoapClient для отправки и приема ws запросов;
    :param token: токен соединения;
    :param camera: номер камеры;
    :param time: время события (в unix формате);
    :param statistic: объект класса Statistic для ведения статистики ошибок и предупреждений.

    :return: словарь ответа вида:
        {
            "img": "base64 code"
        }
    """
    logger = statistic.get_log().get_logger("scripts/ws/analytics")
    logger.info("was called (client: SoapClient, token: str, event: int, time: int, statistic: Statistic)")
    logger.debug("params (client_obj" + token + ", " + str(camera) + ", " + str(time) + ", stat_obf)")

    params, sysparams, method = pattern.faceva_get_frame(token, camera, time)
    response = client.call_method2(method, params, sysparams, [0])

    return response['result'][0]
