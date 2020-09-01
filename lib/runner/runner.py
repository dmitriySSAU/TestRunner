from multiprocessing import Process

from lib.log_and_statistic.log import Log

from lib.runner.db import DataBase
from lib.runner.test_case import TestCase


def run_test_case(tests_config: tuple, runner_config: dict, log: Log) -> None:
    """Целевая функция при запуске дочернего процесса.
    Тест кейс запускается в отдельном дочернем процессе.

    :param tests_config: список настроек теста вида:
    [
        {
            "module": "QML",
            "test": "autoplacemnt",
            "input_data": {},
            "threads": 1,
            "wait_time": 1
        },
        ...
        ...
    ]

    :param runner_config: общие настройки runner;
    :param log: объект класса Log.
    """
    test_case = TestCase(tests_config, runner_config, log)
    test_case.setup()
    test_case.run()
    test_case.teardown()


class Runner:
    """Механизм запуска конфигурации.

    """
    def __init__(self, run_config_id: int, iterations: int, data_base: DataBase, log: Log, runner_settings: dict):
        self._run_config_id = run_config_id
        self._iterations = iterations
        self._data_base = data_base
        self._log = log
        self._runner_settings = runner_settings

        self._test_cases: tuple = data_base.get_run_config_test_cases(run_config_id)

    def start(self) -> None:
        """Метод запуска конфигурации.

        """
        for iteration in range(self._iterations):
            for test_case in self._test_cases:
                tests_config = []
                tests_id = self._data_base.get_test_case_tests(test_case['test_case_id'])
                tests_configs_info = self._data_base.get_tests_configs_info(test_case['test_case_run_config_id'])
                for index, test_id in enumerate(tests_id):
                    test_name: str = self._data_base.get_test_name(test_id)
                    module_name: str = self._data_base.get_module_name(self._data_base.get_module_id(test_id))
                    input_data: dict = self._data_base.get_test_config(test_id, tests_configs_info[index]['id'])
                    tests_config.append({
                        "module": module_name,
                        "test": test_name,
                        "input_data": input_data,
                        "threads": tests_configs_info[index]['threads_count'],
                        "wait_time": tests_configs_info[index]['wait_time']
                    })
                tuple(tests_config)
                test_case_process = Process(target=run_test_case, args=(tests_config, self._runner_settings, self._log))
                test_case_process.start()
                if test_case['wait_finish']:
                    test_case_process.join()
