import argparse

from scripts.common import tools
from multiprocessing import freeze_support

from lib.log_and_statistic.log import Log

from lib.runner import initializer
from lib.runner.db import DataBase
from lib.runner.runner import Runner


def main(run_config_name: str, iterations: int):
    """Функция запуска различной инициализации настроек и тест кейсов.

    """
    initializer.init_settings()

    data_base = DataBase()
    data_base.connect()

    runner_settings = data_base.get_runner_settings()
    log = Log(runner_settings)

    run_config_id: int = data_base.get_run_config_id(run_config_name)
    if run_config_id == -1:
        return
    runner = Runner(run_config_id, iterations, data_base, log, runner_settings)
    runner.start()
    data_base.disconnect()


if __name__ == "__main__":
    # для отключения параллельного запуска приложения после сборки в exe
    # это из-за multiprocessing, полсе запуска exe стартует много парареллельных процессов, вместо одного.
    freeze_support()

    parser = argparse.ArgumentParser()
    parser.add_argument("configuration", help="run configuration's name", type=str)
    parser.add_argument("iterations", help="running configuration's count iterations", type=int)
    args = parser.parse_args()

    main(args.configuration, args.iterations)

