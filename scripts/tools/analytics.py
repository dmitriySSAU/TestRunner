import time

from lib.client.soapClient import SoapClient
from lib.log_and_statistic.statistic import Statistic

from scripts.common import tools

from scripts.ws import decode as ws_decode
from scripts.ws import common as ws_common
from scripts.ws import ewriter as ws_ewriter


def _check_event_comment(event_info: dict, event: dict, statistic: Statistic) -> None:
    """Функция проверки вхождений значений ключей из event_info в event['evtcomment'].
    То есть есть ли указанные значения в комментарии события.

    :param event_info: ключи со значениями, которые надо искать в комментарии;
    :param event: событие (ответ ws);
    :param statistic: объект класса Statistic.
    """
    logger = statistic.get_log().get_logger("scripts/tools/analytics")
    logger.info("was called (event_info: dict, event: dict, statistic: Statistic)")
    logger.debug("params (client_obj, " + str(event_info) + ", " + str(event) + ", stat_obj)")

    for key, value in event_info.items():
        index = event['evtcomment'].find(value)
        if index == -1:
            statistic.append_error("Ожидалось: " + value + ". Получено: " + event['evtcomment'] + "!",
                                   "НЕВАЛИД " + key, False)
        else:
            statistic.append_success("Получено: '" + event['evtcomment'] + "'", "ВАЛИД " + key)


def run_events_test(ws_client: SoapClient, token: str, cam_info: dict, events: tuple, inaccuracy: int, event_type: int,
                    video_source: str, statistic: Statistic) -> None:
    """Функция запуска проверки наличия событий по детектору.
    Каждое событие появляется через определенное время от начала видео. Функция, учитывая погрешность, вычисляет
    интервал времени, в котором должно быть событие и уходит в sleep на это время. После пробуждения проверяет наличие
    события в этом интервале, используя ws метод ewriter:exec с командой select и нужными фильтрами.

    :param ws_client: объект класса SoapClient;
    :param token: токен авторизации;
    :param cam_info: информация по камере (сервер, имя, профиль);
    :param events: список событий из входных данных вида:
                    [
                        {
                            "time": 15,
                            "info": {...}
                        }
                    ]
    см. подробное описание в тестах по аналитике, которые используют данную функцию;
    :param inaccuracy: погрешность для вычисления грациц интервала, в которых должно быть событие;
    :param event_type: номер события;
    :param video_source: путь к видеоисточнику (нужен для удобства вывода сообщений);
    :param statistic: объект класса Statistic.
    """
    if _video_start_expecting(ws_client, token, cam_info, statistic) is False:
        statistic.append_error("Источник: " + video_source + "!", "НЕТ ВИДЕО")
        return
    # Заранее высчитываются временные интервалы,
    # в которых должны находиться события
    start_server_time: str = ws_common.get_current_server_time(ws_client, token, statistic)
    date_start_server_time = tools.get_date_from_str(start_server_time, statistic)
    for event in events:
        event_time = tools.increment_time(date_start_server_time, event['time'])
        left_interval_time_utc = tools.decrement_time(event_time, inaccuracy)
        right_interval_time_utc = tools.increment_time(event_time, inaccuracy)

        left_interval_time = str(tools.convert_time_from_gtc(left_interval_time_utc))[:-9]
        right_interval_time = str(tools.convert_time_from_gtc(right_interval_time_utc))[:-9]

        left_interval_time_utc = str(left_interval_time_utc)
        right_interval_time_utc = str(right_interval_time_utc)

        event.update({
            "start": left_interval_time_utc,
            "end": right_interval_time_utc
        })
    previous_sleep = 0
    for index, event in enumerate(events):
        time.sleep(event['time'] - previous_sleep + inaccuracy)
        result = _check_event_existing(ws_client, token, event['start'], event['end'], event_type, cam_info, statistic)
        if result[0] == 0:
            statistic.append_success("#" + str(index + 1) + " по источнику " + video_source + " в интервале с " +
                                     left_interval_time + " по " + right_interval_time + "!", "ПОЛУЧЕНО СОБЫТИЕ")
            _check_event_comment(event['info'], result[1][0], statistic)
        elif result[0] == -1:
            statistic.append_error("Событие #" + str(index + 1) + " по источнику " + video_source + " в интервале с " +
                                   left_interval_time + " по " + right_interval_time + "!", "НЕТ СОБЫТИЯ")

            time.sleep(inaccuracy / 2)
            current_server_time: str = ws_common.get_current_server_time(ws_client, token, statistic)
            event.update({
                "start": start_server_time,
                "end": current_server_time
            })
            result = _check_event_existing(ws_client, token, event['start'], event['end'], event_type, cam_info,
                                           statistic)
            if result[0] == 0:
                statistic.append_warn("#" + str(index + 1) + " по источнику " + video_source + " в интервале с " +
                                      start_server_time + " по " + current_server_time + "!", "ПОЛУЧЕНО СОБЫТИЕ")
                _check_event_comment(event['info'], result[1][0], statistic)
            elif result[0] > 1:
                statistic.append_error("Событие #" + str(index + 1) + " по источнику " + video_source +
                                       " в интервале с " + start_server_time + " по " + current_server_time + "!",
                                       "МНОГО СОБЫТИй")
            else:
                statistic.append_error(
                    "Событие #" + str(index + 1) + " по источнику " + video_source + " в интервале с " +
                    start_server_time + " по " + current_server_time + "!", "НЕТ СОБЫТИЯ")
        else:
            statistic.append_error("Событие #" + str(index + 1) + " по источнику " + video_source + " в интервале с " +
                                   left_interval_time + " по " + right_interval_time + "!", "МНОГО СОБЫТИй")
        previous_sleep = event['time']


def _video_start_expecting(ws_client: SoapClient, token: str, cam_info: dict, statistic: Statistic) -> bool:
    """Ожидание фактического старта воспроизведения видео.

    Метод опирается на результат ws метода decode:stat. Видео будет считаться начатым,
    если у него битрейт отличен от нуля. Если в течение 30 секунд битрейт не стал больше 0,
    то ожидание прекращается и возвращается False.

    :param ws_client: экземпляр класса SoapClient;
    :param token: логин пользователя.

    :return: флаг успешности старта видео.
    """
    start_time = time.time()
    while True:
        if round((time.time() - start_time)) > 30:
            return False
        stat = ws_decode.decode_stat(ws_client, token, cam_info['server'], cam_info['cam'], cam_info['profile'],
                                     statistic)
        if not stat:
            continue

        bitrate_in = stat[0]['bitrate_in']
        if bitrate_in > 0:
            return True


def _check_event_existing(ws_client: SoapClient, token: str, start_time: str, end_time: str,
                          event_type: int, cam_info: dict, statistic: Statistic) -> tuple:
    """Функция осуществляет проверку наличия определенного типа события в неком временном интервале.

    :param ws_client: экземпляр класса SoapClient;
    :param token: логин пользователя;
    :param start_time: начало интервала;
    :param end_time: конец интервала;
    :param event_type: тип события;
    :param statistic: объект класса Statistic.

    :return: если нет событий, то вернется кортеж (-1, () );
            если есть больше 1 события, то вернется кортеж (кол-во событий, (события) );
            если в интервале 1 события (что хорошо), то вернется кортеж (0, (событие) ).
    """

    events = ws_ewriter.select(ws_client, token, start_time, end_time, None, [event_type], cam_info['server'],
                               cam_info['cam'], cam_info['profile'], statistic)
    if not events:
        return -1, events
    if len(events) > 1:
        return len(events), events
    return 0, events
