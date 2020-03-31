import uuid
from typing import List
import xml.etree.ElementTree as Tree

from requests_patterns.xml import zmq

from scripts.common import tools

from lib.log_and_statistic import log
from lib.client.zmqClient import ZmqClient
from lib.log_and_statistic.statistics import Statistic


def _get_response(zmqclient: ZmqClient, timeout: float):
    """Функкия ожидания ответа.

    :param zmqclient: объект класса ZmqClient
    :param timeout: максимальное ожидание ответа
    :return список с ответами от сервера
    """
    signal_event = zmqclient.get_signal_event()
    signal_event.wait(timeout)
    if signal_event.is_set() is False:
        return -1

    list_xml_responses = zmqclient.get_list_response()
    if len(list_xml_responses) > 0:
        return list_xml_responses


def search_response_index_by_message_id(xml_responses: List[Tree], message_id: str, statistic: Statistic) -> int:
    """Поиск в списке xml у которого значение тега messageId совпадает с message_id.

    :param xml_responses: список xml
    :param message_id: значение тега messageId
    :param statistic: объект класса Statistic
    :return: 1) индекс в списке; 2) -1 в случае отсутствия совпадения
    """
    logger = log.get_logger("scripts/xml/zmq")
    logger.info("was called (list_xml_responses, message_id)")
    logger.debug("(" + str(xml_responses) + ", " + str(message_id) + ")")

    for index, response in enumerate(xml_responses):
        tag_nessage_id = response.find(".//messageId")
        if tag_nessage_id is None:
            statistic.append_error("Отсутствует тег 'messageId'", "ZMQ_ОТВЕТ", True)
        logger.debug("response messageId is " + tag_nessage_id.text)
        if message_id == tag_nessage_id.text:
            logger.info("message_Id is equal!")
            return index
        logger.info("message_Id isn't equal!")
    return -1


def _send_request(zmqclient: ZmqClient, xml_tree_full: Tree, message_id: str, timeout: float,
                  statistic: Statistic) -> Tree:
    """Функция отправки сообщения и с возможностью переотправки.

    :param zmqclient: объект класса ZmqClient
    :param xml_tree_full: запрос дерево XML
    :param message_id: id сообщения
    :param timeout: время ожидания ответа
    :param statistic: объект класса Statistic
    :return: ответ в виде дерева XML
    """
    zmqclient.send_request(xml_tree_full)
    log.print_all("sent request with message_id " + str(message_id))
    send_count = 0

    while True:
        list_xml_responses = _get_response(zmqclient, timeout)
        if list_xml_responses == -1:
            if send_count == 3:
                statistic.append_error("Повторная отправка сообщения '" + str(message_id) + "' завершилась с ошибкой!",
                                       "ZMQ_ОТВЕТ", False)
                break
            zmqclient.send_request(xml_tree_full)
            send_count += 1
            statistic.append_warn("Попытка повторной отправки сообщеия '" + str(message_id), "ZMQ_ОТВЕТ")
            continue
        response_index = search_response_index_by_message_id(list_xml_responses, message_id, statistic)
        if response_index > -1:
            log.print_all("Получен ответ на запрос с id '" + str(message_id) + "'")
            zmqclient.remove_response(message_id)
            return list_xml_responses[response_index]

    return -1


def _common_check_response(xml_response: Tree, method_name: str, statistic: Statistic) -> Tree:
    logger = log.get_logger("scripts/xml/zmq")
    logger.info("was called (xml_response)")
    logger.debug("(" + Tree.tostring(xml_response).decode() + ")")
    if xml_response == -1:
        statistic.append_error(method_name + " завершился с ошибкой!", "ZMQ_ОТВЕТ", False)
        return -1

    status = int(xml_response.find(".//status").text)
    if status != 0:
        status_descr = xml_response.find(".//statusDescr").text
        statistic.append_error("Статус ответа: " + str(status_descr), "ZMQ_ОТВЕТ", False)
        return -1

    return xml_response


def send_hello(zmqclient: ZmqClient, id_: int, timeout: float, statistic: Statistic) -> int:
    """Функция отправки Hello.

    :param zmqclient: объект класса ZmqClient
    :param id_: идентификатор
    :param timeout: максимальное ожидание ответа
    :param statistic: объект класса Statistic
    :return: индекс успешности ответа: 0 - все ок, 1 - ошибка
    """
    message_id = str(uuid.uuid1())
    xml_tree_hello = zmq.hello(message_id, id_)
    xml_tree_full = zmq.common_head(xml_tree_hello)

    xml_response = _send_request(zmqclient, xml_tree_full, message_id, timeout, statistic)
    if xml_response == -1:
        statistic.append_error("Запрос 'Hello' прошел неуспешно!", "ZMQ_ОТВЕТ", False)
        return -1

    log.print_test("Запрос 'Hello' выполнен успешно!")
    return 0


def send_enroll_models(zmqclient: ZmqClient, photo_path: str, timeout: float, statistic: Statistic) -> tuple:
    """Функция отправки EnrollModels.

    :param zmqclient: объект класса ZmqClient
    :param photo_path: путь к фото
    :param timeout: время ожидания ответа
    :param statistic: объект класса Statistic
    :return: дескриптор фото и ее id
    """
    logger = log.get_logger("scripts/xml/zmq")
    logger.info("was called (zmqclient, list_photo_paths, timeout)")

    message_id = str(uuid.uuid1())
    photo_type = tools.get_file_type(photo_path)
    photo_id = str(uuid.uuid1())
    photo_base64 = tools.get_photos_base64([photo_path])[0]
    xml_tree_enroll_models = zmq.enroll_models(message_id, False, photo_base64, photo_type, photo_id)
    xml_tree_full = zmq.common_head(xml_tree_enroll_models)

    xml_response = _common_check_response(_send_request(zmqclient, xml_tree_full, message_id, timeout, statistic),
                                          "EnrollModels", statistic)

    list_faces = xml_response.findall(".//face")
    if not list_faces:
        statistic.append_error("В ответе нет лиц!", "ZMQ_ОТВЕТ", True)
    if len(list_faces) > 1:
        statistic.append_error("Кол-во лиц > 1", "ZMQ_ОТВЕТ", True)

    descriptor = ""
    image_id = xml_response.find(".//image")

    if image_id is None:
        statistic.append_error("Отсутствует тек 'image'!", "ZMQ_ОТВЕТ", False)
    image_id = xml_response.find(".//image").text
    if image_id != photo_id:
        statistic.append_error("ID каритнки не совпадают!", "ZMQ_ОТВЕТ", False)
    for face in list_faces:
        descriptor = face.find(".//model").text
        break

    log.print_test("EnrollModels выполнено успешно!")

    return descriptor, photo_id


def send_add_model_to_hot_list(zmqclient: ZmqClient, model_id: str, descriptor: str, res_num: int, reaction_code: int,
                               archive: int, timeout: float, statistic: Statistic):
    """Функция отправки запроса AddModelToHotList.

    :param zmqclient: объект класса ZmqClient
    :param model_id: id построенной модели
    :param descriptor: дескриптор фото
    :param res_num:
    :param reaction_code:
    :param archive:
    :param timeout: время ожидания ответа
    :param statistic: объект класса Statistic
    :return: -
    """
    logger = log.get_logger("scripts/xml/zmq")
    logger.info("was called (zmqclient, model_id, descriptor, res_num, reaction_code, archive)")

    message_id = str(uuid.uuid1())
    xml_tree_add_to_hot = zmq.add_model_to_hot_list(message_id, model_id, descriptor, res_num, reaction_code, archive)
    xml_tree_full = zmq.common_head(xml_tree_add_to_hot)

    xml_response = _common_check_response(_send_request(zmqclient, xml_tree_full, message_id, timeout, statistic),
                                          "AddToHotlist", statistic)

    return str(message_id)
