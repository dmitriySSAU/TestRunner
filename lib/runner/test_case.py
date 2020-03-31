from lib.log_and_statistic import log

from tests.test_DB import TestDB
from tests.test_QML import TestQML
from tests.test_PTZ import TestPTZ
from tests.test_Users import TestUsers
from tests.test_Server import TestServer
from tests.test_Analytics import TestAnalytics


test_classes = {
    "TestServer": TestServer,
    "TestAnalytics": TestAnalytics,
    "TestQML": TestQML,
    "TestPTZ": TestPTZ,
    "TestDB": TestDB,
    "TestUsers": TestUsers
}


def get_test_case(tests_paths: list) -> list:
    classes_names: list = get_classes_names(tests_paths)
    tests_names: list = get_tests_names(tests_paths)

    test_case: list = []
    for index, test_name in enumerate(tests_names):
        test_case.append({
            "class": classes_names[index],
            "test": test_name
        })

    return test_case


def get_classes_names(tests_paths: list) -> list:
    classes_names: list = []
    for test_path in tests_paths:
        point_index = test_path.find(".")
        classes_names.append(test_path[:point_index])

    return classes_names


def get_tests_names(tests_paths: list) -> list:
    tests_names: list = []
    for test_path in tests_paths:
        point_index = test_path.find(".")
        tests_names.append(test_path[point_index + 1:])

    return tests_names


class TestCase:
    """Класс тест-кейса для запуска тестов внутри него

    """
    def __init__(self, tests_paths: list):
        self._test_case: list = get_test_case(tests_paths)

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
        for test in self._test_case:
            test_class = test_classes[test["class"]]()
            available_tests: dict = test_class.get_tests_methods()
            try:
                test_class.setup()
                available_tests[test["test"]]()
                test_class.teardown()
            except AssertionError as error:
                log.print_error("Тест завершился с ошибкой: " + str(error))

        return True

