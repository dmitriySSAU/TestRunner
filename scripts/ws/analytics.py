from typing import List

from scripts.common import tools

from requests_patterns.ws import analytics as pattern

from lib.log_and_statistic import log
from lib.log_and_statistic.statistics import Statistic

from lib.client.soapClient import SoapClient


def faceva_get_data_base(client: SoapClient, login: str, password: str, statistic: Statistic) -> list:
    """Функция выполнеия ws метода FaceVA:GetDataBase

    :param client: объект класса SoapClient для отправки и приема ws запросов
    :param login: логин пользователя
    :param password: пароль пользователя
    :param statistic: объект класса Statistic для ведения статистики ошибок и предупреждений
    :return: список персон, который приходит в ответе в ключе persons
    """
    logger = log.get_logger("scripts/ws/analytics")
    logger.info("was called(client, login, password)")
    logger.debug("with params (client_obj" + login + ", " + password + ")")

    data = pattern.faceva_get_data_base(login, password)
    response_json = client.call_method2(data[2], data[0], data[1], True)
    logger.debug("response_json: " + str(response_json))
    result = response_json["result"][0]

    tools.check_keys_exist(result, ['persons'], "result", True, statistic)

    persons = result["persons"]
    tools.check_types(["persons"], [persons], [list], statistic)

    if not persons:
        statistic.append_warn("data base persons", "EMPTY")

    for person in persons:
        tools.check_keys_exist(person, ["id", "pacs", "name", 'category', "comment", "information", "department"],
                               'person', True, statistic)

    logger.info("ws method FaceVA:GetDataBase was executed successfully!")
    log.print_all("ws FaceVA:GetDataBase выполнен успешно!")

    return persons


def faceva_update_person(client: SoapClient, login: str, password: str, id_: int, pacs_id: int, name: str, category: str,
                         comment: str, information: str, department: str, faces: List[dict], delete_faces: List[dict],
                         statistic: Statistic) -> str:
    """Функция выполнения ws метода FaceVA:UpdatePerson

    :param client: объект класса SoapClient для отправки и приема ws запросов
    :param login: логин пользователя
    :param password: пароль пользователя
    :param id_: идентификатор персоны в БД
    :param pacs_id: идентификатор персоны в БД для СКД
    :param name: ФИО персоны
    :param category: категория
    :param comment: комментарий
    :param information: информация
    :param department: отдел
    :param faces: список фото лиц для добавления
    :param delete_faces: список фото для удаления
    :param statistic: объект класса Statistic для ведения статистики ошибок и предупреждений
    :return:
    """
    logger = log.get_logger("scripts/ws/analytics")
    logger.info("was called faceva_update_person(client: SoapClient, login: str, password: str, id_: int, pacs_id: int,\
                name: str, category: str, comment: str, information: str, department: str, faces: List[dict], \
                delete_faces: List[dict])")
    logger.debug("faceva_update_person(client_obj" + login + ", " + password + ", " + str(id_) + ", " + str(pacs_id) +
                 ", " + name + ", " + category + ", " + comment + ", " + information + ", " + department + ", " +
                 ", " + str(faces) + ", " + str(delete_faces) + ")")

    data = pattern.faceva_update_person(login, password, id_, pacs_id, name, category, comment, information, department,
                                        faces, delete_faces)
    response_json = client.call_method2(data[2], data[0], data[1], True)
    logger.debug("response_json: " + str(response_json))

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
    log.print_all("ws FaceVA:UpdatePerson выполнен успешно!")

    return person["id"]


# TODO переделать под идентификатор
def faceva_delete_person(client: SoapClient, login: str, password: str, name: str, statistic: Statistic) -> bool:
    """Функция выполнения ws метода FaceVA:DeletePerson

    :param client: объект класса SoapClient для отправки и приема ws запросов
    :param login: логин пользователя
    :param password: пароль пользователя
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
    log.print_test("ws FaceVA:DeletePerson выполнен успешно!")

    return True
