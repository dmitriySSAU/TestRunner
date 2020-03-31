import zmq
import time
import threading
import configparser
from typing import List
import xml.etree.ElementTree as Tree

from lib.log_and_statistic import log

from scripts.xml import zmq as zmq_script


class ZmqClient:
    """Класс-клиент для отправки-приема сообщений по протоколу zmq.

        Реализован механизм многопоточной передачи-приема по одному сокету.
    """
    def __init__(self):
        config = configparser.ConfigParser()
        config.read(log.path + "runner.conf")
        self._sid = config.get("zmq", "sid")
        self._ip = config.get("server", "ip")
        self._port = config.get("server", "port")

        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.PAIR)
        self._socket.connect("tcp://" + self._ip + ":" + self._port)
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

    def get_list_response(self) -> List[Tree]:
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

        index_delete = zmq_script.search_response_index_by_message_id(self._list_responses, message_id)
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
            self.zmqClient = zmqClient
            self.logger = logger

            self.__poller__ = zmq.Poller()
            self.__poller__.register(self.zmqClient.__socket__, zmq.POLLIN)

        def run(self):
            """Механизм приема сообщений.

            :return:
            """
            while True:
                # условие остановки потока
                self.zmqClient.get_handler_thread_destroy_lock().acquire()
                if self.zmqClient._destroy_handler_thread_flag is True:
                    self.zmqClient._destroy_handler_thread_flag = False
                    self.zmqClient.get_handler_thread_destroy_lock().release()
                    return
                self.zmqClient.get_handler_thread_destroy_lock().release()

                # ожидание ответа по сокету
                sockets = dict(self.__poller__.poll())
                if self.zmqClient.__socket__ in sockets:
                    self.zmqClient.__thread_memory_lock__.acquire()
                    str_response = self.zmqClient.__socket__.recv()
                    self.logger.debug("str_response: " + str_response.decode())
                    xml_response = Tree.fromstring(str_response)
                    self.zmqClient.get_list_response().append(xml_response)
                    self.zmqClient.get_signal_event().set()
                    self.zmqClient.get_thread_memory_lock().release()




