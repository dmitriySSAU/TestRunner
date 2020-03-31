from lib.runner import initializer
from lib.runner.test_case import TestCase


class Runner:
    """Механизм запуска тейст-кейсов.

    """
    def __init__(self):
        tests_paths = initializer.init_run_tests()
        self._test_case = TestCase(tests_paths)

    def start(self) -> None:
        self._test_case.setup()
        self._test_case.run()
        self._test_case.teardown()