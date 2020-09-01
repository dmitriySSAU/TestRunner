import sys
import datetime
from typing import List
from termcolor import colored

from lib.log_and_statistic.log import Log


def get_current_time() -> str:
    """Функция получения текущего времени.

    :return: текущее время в виде строки.
    """
    current_time_obj = datetime.datetime.now()
    return current_time_obj.strftime("%d-%m-%Y %H:%M:%S.%f")[:-3]


class Statistic:
    """Класс служит для ведения статистики ошибок по каждому тесту.

    """

    def __init__(self, test_name: str, thread_id: int, config: dict, log: Log):
        self._log = log
        self._logger = log.get_logger("log_and_statistic/statistic")
        self._test_name: str = test_name
        self._thread_id: int = thread_id

        self._errors: List[dict] = []
        self._errors_statistic: List[dict] = []

        self._warns: List[dict] = []
        self._warns_statistic: List[dict] = []

        self._common_statistic: dict = {}

        # максимальное количество идущих подряд ошибок одного типа
        # при достижении которого тест должен завершится
        self._max_errors: int = config['settings']['max_errors']
        self._report: bool = config['settings']['create_report']
        # output_mode - режим вывода сообщений в консоль.
        # Уровни от самого краткого до самого подробного: NONE -> ERROR -> WARN -> TEST -> INFO:
        # NONE - отключить вывод.
        # ERROR - только ошибки.
        # WARN - ошибки и предупреждения.
        # TEST - ошибки, предупреждения и различные информативные сообщения, связанные непосредственно с тестами.
        # INFO - вывод всего, в том числе подробной информативной информации.
        self._output_mode = config['settings']['output_mode']
        self._error_in_row_count: int = 0
        self._error_in_row_type: str = ""

    def get_log(self) -> Log:
        """Метод-геттер экземпляра класса Log.

        :return: экземпляр класса Log.
        """
        return self._log

    def show_errors_statistic(self) -> None:
        """Вывод краткой статистики по ишибкам.

        """
        self._error("\n========================================================================================" +
                    "\n             ТЕСТ " + self._test_name + "[Поток #" + str(self._thread_id) + "]" +
                    "\n========================================================================================")

        for err_stat in self._errors_statistic:
            self._error("[" + err_stat["type"] + "]: " + str(err_stat["count"]))

        self._error("\nСписок ошибок:")
        for index, error in enumerate(self._errors):
            self._error(str(index + 1) + ". [" + error['time'] + "] [" + error['type'] + "] " + error['message'])

    def show_warns_statistic(self, show_warn_list: bool = False) -> None:
        """Вывод краткой статистики по предупреждением.

        """
        self._warn("\n========================================================================================" +
                   "\n             ТЕСТ " + self._test_name + "[Поток #" + str(self._thread_id) + "]" +
                   "\n========================================================================================")

        for warn_stat in self._warns_statistic:
            self._warn("[" + warn_stat["type"] + "]: " + str(warn_stat["count"]))

        if show_warn_list:
            self._warn("\nСписок предупреждений:")
            for index, warn in enumerate(self._warns):
                self._warn(str(index + 1) + ". [" + warn['time'] + "] [" + warn['type'] + "] " + warn['message'])

    def show_common_statistic(self) -> None:
        """Вывод краткой статистики по предупреждением.

        """
        self._info("\n========================================================================================" +
                   "\n         ОБЩАЯ СТАТИСТИКА" +
                   "\n========================================================================================")

        for comm_stat_key in self._common_statistic:
            self._info(comm_stat_key + ": " + str(self._common_statistic[comm_stat_key]))

    def append_error(self, message: str, type_: str, critical: bool = False) -> None:
        """Добавлеие ошибки и ее типа в список, а также вывод в консоль сообщения о ней.

        :param message: сообщение ошибки;
        :param type_: тип ошибки;
        :param critical: флаг критической ошибки. Если True, то происходит остановка теста.
        """
        self._logger.info("was called (message: str, type_: str, is_critical: bool)")
        self._logger.debug("with params (" + message + ", " + type_ + ", " + str(critical) + ")")

        current_time = get_current_time()
        self._errors.append({
            "message": message,
            "type": type_,
            "time": current_time
        })

        self._error("\n[" + current_time + "][Поток #" + str(self._thread_id) + "][" + type_ + "]\n" + message)
        self._compute_errors_statistic(type_)
        self._compute_error_in_row(type_)

        if self._error_in_row_count >= self._max_errors:
            sys.exit("Превышен лимит ошибок типа [" + type_ + "]!")
        if critical:
            sys.exit("\n[" + type_ + "] " + message)

    def append_warn(self, message: str, type_: str) -> None:
        """Добавлеие предупреждения и его типа в список, а также вывод в консоль сообщения о нем.

        :param message: сообщение предупреждения;
        :param type_: тип предупреждения.
        """
        self._logger.info("was called (message: str, type_: str)")
        self._logger.debug("params (" + message + ", " + type_ + ")")

        current_time = get_current_time()
        self._warns.append({
            "message": message,
            "type": type_,
            "time": current_time
        })
        self._warn("\n[" + current_time + "][Поток #" + str(self._thread_id) + "][" + type_ + "]\n" + message)
        self._compute_warns_statistic(type_)

    def append_info(self, message: str, type_: str) -> None:
        """Добавление вспомогательной информации и его типа в список, а также вывод в консоль сообщения о ней.

        :param message: сообщение информации;
        :param type_: тип информации.
        """
        self._logger.info("was called (message: str, type_: str)")
        self._logger.debug("params (" + message + ", " + type_ + ")")

        current_time = get_current_time()
        self._info("\n[" + current_time + "][Поток #" + str(self._thread_id) + "][" + type_ + "]\n" + message)

    def append_success(self, message: str, type_: str):
        """Добавление информации о успешной проверке/теста в список, а также вывод в консоль сообщения о ней.

        :param message: сообщение теста;
        :param type_: тип теста.
        """
        self._logger.info("was called (message: str, type_: str)")
        self._logger.debug("params (" + message + ", " + type_ + ")")

        current_time = get_current_time()
        self._test("\n[" + current_time + "][Поток #" + str(self._thread_id) + "][" + type_ + "]\n" + message)

        self._error_in_row_type = ""
        self._error_in_row_count = 0

    def create_report(self) -> None:
        """Метод создания отчета.
        Создает файл report.txt в корне приложения и записывает в него
        список ошибок и предупреждений по каждому тесту.

        """
        with open("./report[" + self._test_name + "].txt", "a", encoding="utf-8") as report_file:
            report_file.write("\n==================================================================================="
                              "=====" + "\n             ТЕСТ " + self._test_name + "[Поток #" + str(self._thread_id) + "]" +
                              "\n================================================================================"
                              "========\n")

            for err_stat in self._errors_statistic:
                report_file.write("[" + err_stat["type"] + "]: " + str(err_stat["count"]) + "\n")

            report_file.write("\nСписок ошибок:\n")
            for index, error in enumerate(self._errors):
                report_file.write(str(index + 1) + ". [" + error['time'] + "] [" + error['type'] + "] " +
                                  error['message'] + "\n")

    def _compute_error_in_row(self, type_: str):
        if type_ == self._error_in_row_type:
            self._error_in_row_count += 1
        else:
            self._error_in_row_type = type_
            self._error_in_row_count = 1

    def _compute_errors_statistic(self, type_: str) -> None:
        for err_stat in self._errors_statistic:
            if err_stat["type"] == type_:
                err_stat["count"] += 1
                return

        self._errors_statistic.append({
            "type": type_,
            "count": 1
        })

    def _compute_warns_statistic(self, type_: str) -> None:
        for warn_stat in self._warns_statistic:
            if warn_stat["type"] == type_:
                warn_stat["count"] += 1
                return

        self._warns_statistic.append({
            "type": type_,
            "count": 1
        })

    def _test(self, message: str) -> None:
        """Вывод в консоль сообщения уровня TEST.
        Вывод имеет зеленый цвет.

        :param message: текст сообщения для вывода.
        """
        if self._output_mode == "TEST" or self._output_mode == "INFO":
            print(colored(message, "green"))

    def _warn(self, message: str) -> None:
        """Вывод в консоль сообщения уровня WARN.
        Вывод имеет желтый цвет.

        :param message: текст сообщения для вывода.
        """
        if self._output_mode == "WARN" or self._output_mode == "TEST" or self._output_mode == "INFO":
            print(colored(message, "yellow"))

    def _error(self, message: str) -> None:
        """Вывод в консоль сообщения уровня ERROR.
        Вывод имеет красного цвет.

        :param message: текст сообщения для вывода.
        """
        if self._output_mode != "NONE":
            print(colored(message, "red"))

    def _info(self, message: str) -> None:
        """Вывод в консоль сообщения уровня INFO.
        Вывод имеет стандартный цвет (белый).

        :param message: текст сообщения для вывода.
        """
        if self._output_mode == "INFO":
            print(message)
