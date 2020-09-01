import zmq
import time
import threading
from typing import List
import xml.etree.ElementTree as Tree

from lib.log_and_statistic import log
from lib.log_and_statistic.statistic import Statistic


def search_response_index_by_message_id(xml_responses: list, message_id: str, statistic: Statistic) -> int:
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


class ZmqClient:
    """Класс-клиент для отправки-приема сообщений по протоколу zmq.

        Реализован механизм многопоточной передачи-приема по одному сокету.
    """
    def __init__(self, config: dict, statistic: Statistic):
        self._sid = config['zmq']['sid']
        self._ip = config['server']['ip']
        self._port = config['server']['zmq_port']
        self._statistic = statistic

        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.PAIR)
        self._socket.connect("tcp://" + self._ip + ":" + str(self._port))
        self._list_responses = []
        self._handler_thread = None
        # блокировка для раннего уничтожения объекта потока
        # если вызвали send_request, а поток хочет завершится, то завершения не произойдет
        self._handler_thread_destroy_lock = threading.Lock()
        self._destroy_handler_thread_flag = False
        # блокировка для одновременного доступа к памяти - листу __list_responses__ и сокету
        self._thread_memory_lock = threading.Lock()
        # механизм для ожидания сообщения вызывающими потоками
        self._signal_event = threading.Event()
        self._signal_event.clear()
        self._logger = log.get_logger("client/zmqClient")

    def get_signal_event(self) -> threading.Event:
        return self._signal_event

    def get_handler_thread_destroy_lock(self) -> threading.Lock:
        return self._handler_thread_destroy_lock

    def get_destroy_hadler_thread_flag(self) -> bool:
        return self._destroy_handler_thread_flag

    def get_thread_memory_lock(self) -> threading.Lock:
        return self._thread_memory_lock

    def get_list_response(self) -> list:
        """Получить список всех текущих ответов.

        :return: список ответов _list_responses
        """
        self._thread_memory_lock.acquire()
        current_list_response = list(self._list_responses)
        self._thread_memory_lock.release()

        return current_list_response

    def remove_response(self, message_id: str) -> int:
        """Удалить ответ из списка ответов по его message_id.

        :param message_id: тег xml messageId в ответе
        :return: 0 - успех; 1 - ошибка (ответ с таким messageId не найдет)
        """
        self._thread_memory_lock.acquire()

        index_delete = 0
        search_response_index_by_message_id(self._list_responses, message_id, self._statistic)
        if index_delete != -1:
            self._list_responses.pop(index_delete)
            self._thread_memory_lock.release()
            if not self._list_responses:
                self._signal_event.clear()
            return 0
        else:
            self._thread_memory_lock.release()
            return -1

    def start_handler_thread(self):
        """Метод запускает отдельный поток приема сообщений по сокету.

        :return: 0
        """
        if self._handler_thread is None:
            self._handler_thread = self.SocketThread(self, self._logger)
            self._handler_thread.start()
        else:
            if self._handler_thread.isAlive() is False:
                self._handler_thread.start()

        return 0

    def stop_handler_thread(self):
        """Метод останавливает отдельный поток приема сообщений по сокету.

        :return: 0 - успех; 1 - ошибка
        """
        self._handler_thread_destroy_lock.acquire()
        self._destroy_handler_thread_flag = True
        self._handler_thread_destroy_lock.release()

        time.sleep(0.5)

        self._handler_thread_destroy_lock.acquire()
        if self._destroy_handler_thread_flag is False:
            self._handler_thread_destroy_lock.release()
            return 0
        else:
            return 1

    def send_request(self, xml_tree):
        """Отправка нового сообщения по сокету.

        Если поток приема ответа не создан, то он создается и запускается.
        Если поток уже создан, но не активен, то он запускается.
        :param xml_tree: сформированное дерево xml
        :return: 1
        """
        # проверка на возможность приема сообщения
        if self._handler_thread is None:
            log.raise_error("Handler thread isn't exist!", self._logger)
        if self._handler_thread.isAlive() is False:
            log.raise_error("Handler thread isn't run!", self._logger)

        request_msg = '<?xml version="1.0" encoding="UTF-8"?>' + Tree.tostring(xml_tree).decode()

        self._logger.info("was called func send_request(request_msg)")
        self._logger.debug("send_request(" + str(request_msg) + ")")
        # установка блокировки для объекта сокета
        self._thread_memory_lock.acquire()

        self._logger.info("acquired __thread_memory_lock__")
        self._logger.debug("current msg is " + str(request_msg))
        self._socket.send_string(request_msg)

        self._thread_memory_lock.release()
        self._logger.info("release __thread_memory_lock__")

        return 1

    class SocketThread(threading.Thread):
        """ Класс для реализации многопоточного приема по одному сокету.
        """
        def __init__(self, zmqClient, logger):
            threading.Thread.__init__(self, daemon=True)
            self._zmqClient = zmqClient
            self._logger = logger

            self._poller = zmq.Poller()
            self._poller.register(self._zmqClient._socket, zmq.POLLIN)

        def run(self):
            """Механизм приема сообщений.

            :return:
            """
            while True:
                # условие остановки потока
                self._zmqClient.get_handler_thread_destroy_lock().acquire()
                if self._zmqClient._destroy_handler_thread_flag is True:
                    self._zmqClient._destroy_handler_thread_flag = False
                    self._zmqClient.get_handler_thread_destroy_lock().release()
                    return
                self._zmqClient.get_handler_thread_destroy_lock().release()

                # ожидание ответа по сокету
                sockets = dict(self._poller.poll())
                if self._zmqClient._socket in sockets:
                    self._zmqClient._thread_memory_lock.acquire()
                    str_response = self._zmqClient._socket.recv()
                    self._logger.debug("str_response: " + str_response.decode())
                    xml_response = Tree.fromstring(str_response)
                    self._zmqClient._list_responses.append(xml_response)
                    self._zmqClient.get_signal_event().set()
                    self._zmqClient.get_thread_memory_lock().release()




