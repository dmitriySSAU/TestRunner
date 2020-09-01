import time
import threading

from lib.log_and_statistic.log import Log
from lib.log_and_statistic.statistic import Statistic


from tests.test_DB import TestDB
from tests.test_Web import TestWeb
from tests.test_QML import TestQML
from tests.test_PTZ import TestPTZ
from tests.test_Media import TestMedia
from tests.test_Users import TestUsers
from tests.test_Server import TestServer
from tests.test_Ewriter import TestEwriter
from tests.test_Analytics import TestAnalytics
from tests.test_Common import TestCommon


test_classes = {
    "Server": TestServer,
    "Analytics": TestAnalytics,
    "QML": TestQML,
    "PTZ": TestPTZ,
    "DB": TestDB,
    "Users": TestUsers,
    "Ewriter": TestEwriter,
    "Web": TestWeb,
    "Media": TestMedia,
    "Common": TestCommon
}


class TestCase:
    """Класс тест-кейса для запуска тестов внутри него

    """
    def __init__(self, tests_config: tuple, runner_config: dict, log: Log):
        self._tests_config: tuple = tests_config
        self._runner_config = runner_config
        self._log = log

    def setup(self):
        """Функция будет вызываться перед запуском каждого тест кейса

        :return:
        """
        return True

    def teardown(self):
        """Функция будет вызываться после окончания тест кейса.

        :return:
        """
        return True

    def run(self):
        """Запуск тест кейса.

        :return:
        """

        test_case_statistic = Statistic("Тест-кейс", 1, self._runner_config, self._log)
        test_threads: list = []

        for test in self._tests_config:
            test_case_statistic.append_success("----------------------------------ТЕСТ " + test['module'] + "." +
                                               test['test'] + "------------------------------------", "ЗАПУСК")
            for thread in range(test['threads']):
                test_threads.append(self.TestRunner(thread + 1, test['module'], test['test'], test['input_data'],
                                                    self._runner_config, self._log))
            for thread in test_threads:
                thread.start()
            for thread in test_threads:
                thread.join()
            test_case_statistic.append_success("----------------------------------ТЕСТ " + test['module'] + "." +
                                               test['test'] + "------------------------------------", "ЗАВЕРШЕНИЕ")
            for thread in test_threads:
                statistic = thread.get_statistic()
                statistic.show_errors_statistic()
                statistic.show_warns_statistic()
                if self._runner_config['settings']['create_report']:
                    statistic.create_report()
            test_threads.clear()
            time.sleep(test['wait_time'])
        return True

    class TestRunner(threading.Thread):
        """Класс для запуска тесте из тест кейса в отдельном потоке.

        """
        def __init__(self, thread_id: int, module: str, test: str, input_data: dict, config: dict, log: Log):
            threading.Thread.__init__(self)
            self._statistic = Statistic(test, thread_id, config, log)

            self._test_class = test_classes[module](input_data, config, self._statistic)
            self._test = test
            self._id = str(thread_id)

        def get_statistic(self):
            """Метод-геттер получения объекта статистики.

            :return:
            """
            return self._statistic

        def run(self):
            """Переопределенный метод запуска потока.

            """
            full_test_name = self._test + "[Поток #" + self._id + "]"
            test_method = getattr(self._test_class, self._test)
            error_msg = ""
            try:
                self._test_class.setup()
                test_method()
            except SystemExit as e:
                error_msg = e.args[0]
            self._test_class.teardown()

            if error_msg:
                self._statistic.append_error("Тест " + full_test_name + " завершился с критической ошибкой: "
                                             + error_msg, "КРИТ")
            else:
                self._statistic.append_success("Тест " + full_test_name + " завершился без критических ошибок!",
                                               "УСПЕХ")
