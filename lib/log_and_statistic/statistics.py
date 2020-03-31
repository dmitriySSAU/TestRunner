import time
import configparser
from typing import List

from lib.log_and_statistic import log


class Statistic:
    """Класс служит для ведения статистики ошибок по каждому тесту.

    """

    def __init__(self):
        self._logger = log.get_logger("log_and_statistic\\statistic")

        self._errors: List[dict] = []
        self._errors_statistic: List[dict] = []

        self._warns: List[dict] = []
        self._warns_statistic: List[dict] = []

        self._common_statistic: dict = {}

        config = configparser.ConfigParser()
        config.read(log.path + "\\runner.conf")
        # максимальное количество идущих подряд ошибок одного типа
        # при достижении которого тест должен завершится
        self._max_errors: int = int(config.get("settings", "max_error_in_row"))

    def show_errors_statistic(self) -> None:
        """Вывод краткой статистики по ишибкам.

        """
        log.print_error("\n============================================")
        log.print_error("            СТАТИСТИКА ОШИБОК")
        log.print_error("============================================")

        for err_stat in self._errors_statistic:
            log.print_error("[" + err_stat["type"] + "]: " + str(err_stat["count"]))
        self._errors.clear()
        time.sleep(0.1)

    def show_warns_statistic(self) -> None:
        """Вывод краткой статистики по предупреждением.

        """
        log.print_warn("\n============================================")
        log.print_warn("         СТАТИСТИКА ПРЕДУПРЕЖДЕНИЙ")
        log.print_warn("============================================")

        for warn_stat in self._warns_statistic:
            log.print_warn("[" + warn_stat["type"] + "]: " + str(warn_stat["count"]))
        self._warns.clear()
        time.sleep(0.1)

    def show_common_statistic(self) -> None:
        """Вывод краткой статистики по предупреждением.

        """
        log.print_all("\n============================================")
        log.print_all("            ОБЩАЯ СТАТИСТИКА")
        log.print_all("============================================")

        for comm_stat_key in self._common_statistic:
            log.print_all(comm_stat_key + ": " + str(self._common_statistic[comm_stat_key]))
        time.sleep(0.1)

    #def show_errors(self):

    #def show_warnings(self):

    def append_error(self, message: str, type_: str, is_critical: bool) -> None:
        """Добавлеие ошибки и ее типа в список, а также вывод в консоль сообщения о ней.

        :param message: сообщение ошибки
        :param type_: тип ошибки
        :param is_critical: флаг критической ошибки. Если True, то тест завершается
        """
        self._logger.info("was called (message: str, type_: str, is_critical: bool)")
        self._logger.debug("with params (" + message + ", " + type_ + ", " + str(is_critical) + ")")

        self._errors.append({
            "message": message,
            "type": type_
        })
        log.print_error("[" + type_ + "] " + message)
        self._compute_errors_statistic(type_)

        if self._compute_count_one_type_errors_in_row(type_) >= self._max_errors:
            log.raise_error("Превышен лимит ошибок типа [" + type_ + "]!", self._logger)

        if is_critical:
            log.raise_error("[" + type_ + "] " + message, self._logger)

    def append_warn(self, message: str, type_: str) -> None:
        """Добавлеие предупреждения и его типа в список, а также вывод в консоль сообщения о нем.

            :param message: сообщение ошибки
            :param type_: тип ошибки
        """
        self._logger.info("was called (message: str, type_: str)")
        self._logger.debug("with params (" + message + ", " + type_ + ")")

        self._warns.append({
            "message": message,
            "type": type_
        })
        log.print_warn("[" + type_ + "] " + message)
        self._compute_warns_statisitc(type_)

    def set_common_statistic(self, statistic: dict) -> None:
        self._common_statistic = statistic

    def get_common_statistic(self) -> dict:
        return self._common_statistic

    def _compute_count_one_type_errors_in_row(self, type_: str) -> int:
        temp_errors: List[dict] = list(self._errors)
        temp_errors.reverse()
        count = 0
        for error in temp_errors:
            if error["type"] == type_:
                count += 1
            else:
                break
        return count

    def _compute_errors_statistic(self, type_: str) -> None:
        for err_stat in self._errors_statistic:
            if err_stat["type"] == type_:
                err_stat["count"] += 1
                return

        self._errors_statistic.append({
            "type": type_,
            "count": 1
        })

    def _compute_warns_statisitc(self, type_: str) -> None:
        for warn_stat in self._warns_statistic:
            if warn_stat["type"] == type_:
                warn_stat["count"] += 1
                return

        self._warns_statistic.append({
            "type": type_,
            "count": 1
        })
