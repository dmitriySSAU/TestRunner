import json
import sqlite3


class DataBase:
    """Класс по работе с баззой данных Runner.

    """
    def __init__(self):
        self._DB_PATH = "./databases/runner.db"
        self._connection = None
        self._cursor = None

    def connect(self) -> None:
        """Метод соединения с БД.

        """
        self._connection = sqlite3.connect(self._DB_PATH)
        self._cursor = self._connection.cursor()

    def disconnect(self) -> None:
        """Метод отсоединения от БД.

        """
        self._connection.close()

    def get_runner_settings(self) -> dict:
        """Метод получения общих настроек Runner.

        :return: словарь с настройками.
        """
        sql_cmd = "SELECT settings FROM Settings WHERE type = ?"
        self._cursor.execute(sql_cmd, [1])
        settings = self._cursor.fetchall()[0][0]

        return json.loads(settings)

    def get_run_config_id(self, run_config_name: str) -> int:
        """Метод получения первичного ключа конфигурации запуска.
        Первичный ключ из таблицы RunConfiguration извлекается по
        имени конфигурации запуска, так как атрибут name является
        альтернативным ключем.

        :param run_config_name: имя конфигурации запуска.

        :return: первичный ключ (id) конфигурации запуска.
        """
        sql_cmd = "SELECT idRunConfig FROM RunConfiguration WHERE name = ?"
        self._cursor.execute(sql_cmd, [run_config_name])
        result: tuple = self._cursor.fetchall()
        assert result, "Конфигурация запуска с именем " + run_config_name + " отсутствует!"

        return result[0][0]

    def get_run_config_test_cases(self, run_config_id: int) -> tuple:
        """метод получения первичных ключей и атрибута waitFinish тест кейсов.
        Запрос осуществляется в таблицу TestCaseRunConfiguration, который возвращает
        строки в порядке sequenceNumber по конкретной конфигурации запуска.

        :param run_config_id: id (первичный ключ) конфигурации запуска.

        :return: кортеж тест кейсов вида:
                (
                    {
                        "test_case_run_config_id": 0
                        "test_case_id": 0,
                        "wait_finish": 1
                    },
                    ...
                    ...
                )
        """
        sql_cmd = "SELECT idTestCaseConfig, idTestCase, waitFinish FROM TestCaseRunConfiguration WHERE idRunConfig = ?" \
                  " ORDER BY sequenceNumber"
        self._cursor.execute(sql_cmd, [run_config_id])
        result: tuple = self._cursor.fetchall()
        assert result, "[0001] Не добавлено ни одного тест кейса для указанной конфигурации запуска!"

        test_cases = []
        for test_case in result:
            test_cases.append({
                "test_case_run_config_id": test_case[0],
                "test_case_id": test_case[1],
                "wait_finish": bool(test_case[2])
            })

        return tuple(test_cases)

    def get_test_case_tests(self, test_case_id: int) -> tuple:
        """Метод получения списка id тестов в тест кейсе.
        Запрос осуществляется в таблицу TestCaseTestRelation по id тест кейса в порядке sequenceNumber.

        :param test_case_id: id (первичный ключ) тест кейса.

        :return: кортеж id (первичных ключей) тестов.
        """
        sql_cmd = "SELECT idTest FROM TestCaseTestRelation WHERE idTestCase = ? ORDER BY sequenceNumber"
        self._cursor.execute(sql_cmd, [test_case_id])
        result: tuple = self._cursor.fetchall()
        assert result, "[0002] Не добавлено ни одного теста в тест кейс!"

        tests_id = []
        for test_id in result:
            tests_id.append(test_id[0])

        return tuple(tests_id)

    def get_tests_configs_info(self, test_case_run_config_id: int) -> tuple:
        """Метод получения списка конфигураций теста.
        Запрос осуществляется в таблицу TestRunConfiguration, таким образом для каждого теста
        с помощью использования sequenceNumber определяется id конфигурации (вх. данные).

        :param test_case_run_config_id: id (первичный ключ) строки из таблицы TestCaseRunConfiguration.

        :return: список вида:
                (
                    {
                        "id": 0,
                        "threads_count": 1,
                        "wait_time": 0
                    },
                    ...
                    ...
                )
        """
        sql_cmd = "SELECT idTestConfig, threadsCount, waitTime FROM TestRunConfiguration WHERE idTestCaseConfig = ? " \
                  "ORDER BY sequenceNumber"
        self._cursor.execute(sql_cmd, [test_case_run_config_id])
        result: tuple = self._cursor.fetchall()
        assert result, "[0003] Не добавлено ни одной конфигурации теста в конфигурации запуска!"

        test_configs = []
        for test_config in result:
            test_configs.append({
                "id": test_config[0],
                "threads_count": test_config[1],
                "wait_time": test_config[2]
            })

        return tuple(test_configs)

    def get_test_config(self, test_id: int, config_id: int) -> dict:
        """Метод получения сохраненной конфигурации для теста (json|input_data).
        Запрос осуществлеятся в таблице TestConfiguration. Получение значения атрибута
        inputData.

        :param test_id: id (первичный ключ) теста;
        :param config_id: id (первичный ключ) конфига.

        :return: словарь с входными данными для теста.
        """
        sql_cmd = "SELECT inputData FROM TestConfiguration WHERE idTest = ? AND idTestConfig = ?"
        self._cursor.execute(sql_cmd, [test_id, config_id])
        result: tuple = self._cursor.fetchall()
        assert result, "[0004] Указанной конфигурации нет в таблице для данного теста!"

        return json.loads(result[0][0])

    def get_test_name(self, test_id: int) -> str:
        """Метод получения имени теста по его id (первичном ключу).

        :param test_id: id (первичный ключ) теста.

        :return: имя теста.
        """
        sql_cmd = "SELECT name FROM Test WHERE idTest = ?"
        self._cursor.execute(sql_cmd, [test_id])
        result: tuple = self._cursor.fetchall()
        assert result, "[0005] Теста с указанным id не существует!"

        return result[0][0]

    def get_module_id(self, test_id: int) -> int:
        """Метод получения id (первичного ключа) модуля по id теста.

        :param test_id: id (первичный ключ) теста.

        :return: id модуля.
        """
        sql_cmd = "SELECT idModule FROM Test WHERE idTest = ?"
        self._cursor.execute(sql_cmd, [test_id])
        result: tuple = self._cursor.fetchall()
        assert result, "[0006] Теста с указанным id не существует!"

        return result[0][0]

    def get_module_name(self, module_id: int) -> str:
        """Метод получения имени модуля по его id (первичному ключу).

        :param module_id: id (первичный ключ) модуля.

        :return: имя модуля.
        """
        sql_cmd = "SELECT name FROM Module WHERE idModule = ?"
        self._cursor.execute(sql_cmd, [module_id])
        result: tuple = self._cursor.fetchall()
        assert result, "[0007] Модуля с указанным id не существует!"

        return result[0][0]
