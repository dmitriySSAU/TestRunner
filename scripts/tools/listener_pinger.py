from lib.log_and_statistic.statistic import Statistic

from scripts.common import tools


def compare_local_servers(string: dict, template_string: dict, local_server_ip: str, statistic: Statistic) -> bool:
    """Функция сравнивает значения всех ключей поля string из ws метода listener_pinger_get_local_servers
     с другим таким же словарем.

    Оба словаря должны быть равны значению ключа string из ws метода listener_pinger_get_local_servers или
    listener_pinger_get_down_servers

    :param string: строка ответа;
    :param template_string: эталонная строка;
    :param local_server_ip: ip локального сервера;
    :param statistic: объект класса Statistic.

    :return: флаг корректности.
    """
    is_correct = True

    if string == template_string:
        return is_correct

    checked_keys: list = []
    for template_key in template_string.keys():
        if template_key not in string:
            statistic.append_error(template_key + " в 'string' у " + local_server_ip + "!", "НЕТ КЛЮЧА")
            continue

        checked_keys.append(template_key)

        if template_key == "cams":
            if template_string["cams"] == string["cams"]:
                continue

            if not template_string["cams"] and string["cams"]:
                statistic.append_warn("Список камер у сервера " + local_server_ip + " не пустой!", "ЕСТЬ КАМЕРЫ")
                continue

            if not string["cams"] and template_string["cams"]:
                statistic.append_error("Сервер " + local_server_ip + "!", "НЕТ КАМЕР")
                is_correct = False
                continue

            # ищем камеру, которая отсутствует
            # либо ищем отличие в конкретных ключах у камеры
            # также ищем какие ключи отсутствуют в шаблоне, но есть по факту
            for template_cam in template_string["cams"]:
                # проверка на отсутствие камеры
                string_cam_index = tools.get_dict_by_keys_values(string["cams"], ["key2", "key3"],
                                                                 [template_cam["key2"], template_cam["key3"]])
                if string_cam_index == -1:
                    statistic.append_error(template_cam["key2"] + "(" + template_cam["key3"] + ") на сервере "
                                           + local_server_ip + "!", "НЕТ КАМЕРЫ")
                    is_correct = False
                    continue

                if template_cam == string["cams"][string_cam_index]:
                    continue

                # поиск отличий в конкретных ключах у камеры
                for template_cam_key in template_cam:
                    if template_cam_key not in string["cams"][string_cam_index]:
                        statistic.append_error(template_cam_key + " в " + template_cam + " на сервере " +
                                               local_server_ip + "'!", "НЕТ КЛЮЧА ПО КАМЕРЕ")
                        is_correct = False
                        continue
                    current_key_value = string["cams"][string_cam_index][template_cam_key]
                    if template_cam[template_cam_key] != current_key_value and template_cam_key != "Status":
                        statistic.append_error(template_cam_key + " в камере " + template_cam["key2"] + "(" +
                                               template_cam["key3"] + ") на сервере " + local_server_ip + "!" +
                                               " Требуется: " + str(template_cam[template_cam_key]) +
                                               "(" + str(current_key_value) + ")!", "НЕВАЛИД ЗНАЧ")
                        is_correct = False
                        continue

                # поиск отсутствующих ключей в шаблоне
                for string_cam_key in string["cams"][string_cam_index]:
                    if string_cam_key not in template_cam:
                        statistic.append_warn(string_cam_key + " в камере " + template_cam +
                                              " на сервере" + local_server_ip + " в ШАБЛОНЕ!", "НЕТ КЛЮЧА")
            # ищем камеры, которых нет в шаблоне
            # но есть по факту
            for string_cam in string["cams"]:
                string_cam_is_in_template = False
                for template_cam in template_string["cams"]:
                    if string_cam["key2"] == template_cam["key2"]:
                        string_cam_is_in_template = True
                        break
                if string_cam_is_in_template is False:
                    statistic.append_warn(string_cam["key2"] + " на сервере " + local_server_ip +
                                          " в ШАБЛОНЕ!", "НЕТ КАМЕРЫ")

        elif template_key == "archive":
            if template_string[template_key] == string[template_key]:
                continue

            if not template_string[template_key] and string[template_key]:
                statistic.append_warn("Сервер " + local_server_ip, "ЕСТЬ АРХИВ")
                #is_correct = False
                continue

            if not string[template_key] and template_string[template_key]:
                statistic.append_error("Сервер " + local_server_ip, "НЕТ АРХИВА")
                is_correct = False

            for archive in template_string[template_key][0]:
                if string[template_key][0].count(archive) > 0:
                    continue
                else:
                    statistic.append_error(str(archive) + " на сервере " + local_server_ip, "НЕТ АРХИВА")
                    is_correct = False

            for archive in string[template_key][0]:
                if template_string[template_key][0].count(archive) > 0:
                    continue
                else:
                    statistic.append_warn(str(archive) + " на сервере " + local_server_ip, "НЕТ АРХИВА")
                    is_correct = False

        else:
            if string[template_key] != template_string[template_key] and template_key != "down_servers":
                statistic.append_error(str(string[template_key]) + " по ключу" + template_key + " на сервере "
                                       + local_server_ip + "! Требуется: " + str(template_string[template_key]) +
                                       "(" + str(string[template_key]) + ")!", "НЕВАЛИД ЗНАЧ")
                is_correct = False

    return is_correct


def compare_down_servers(string: dict, template_string: dict, main_server_ip: str, statistic: Statistic) -> bool:
    """Функция проверки эквивалентности "нижних" серверов

    :param string: строка ответа;
    :param template_string: эталонная строка;
    :param main_server_ip: ip главного сервера;
    :param statistic: объект класса Statistic.

    :return: флаг корректности.
    """
    is_correct = True

    if string == template_string:
        return is_correct

    if compare_local_servers(string, template_string, main_server_ip, statistic) is False:
        statistic.append_info("Локальный сервер некорректен в ответе 'get_down' на сервере " + main_server_ip,
                              "СРАВНЕНИЕ")
        is_correct = False

    if string["down_servers"] == template_string["down_servers"]:
        return is_correct
    if not string["down_servers"] and template_string["down_servers"]:
        statistic.append_error("Сервер " + main_server_ip + "!", "НЕТ НИЖНИХ СЕРВЕРОВ")
        is_correct = False
    if not template_string["down_servers"] and string["down_servers"]:
        statistic.append_warn("Сервер " + main_server_ip + "!", "ЕСТЬ НИЖНИЕ СЕРВЕРА")
        #is_correct = False

    # проход по шаблону и поиск отличий
    down_servers_names: list = get_down_servers_names(string["down_servers"])
    for template_down_server in template_string["down_servers"]:
        template_down_server_name: str = list(template_down_server.keys())[0]
        statistic.append_info("Сравнение нижнего сервера " + template_down_server_name + " с шаблоном...", "ИНФО")
        if template_down_server_name not in down_servers_names:
            statistic.append_error(template_down_server_name + " на сервере" + main_server_ip + "!",
                                   "НЕТ НИЖНЕГО СЕРВЕРА")
            is_correct = False
            continue
        down_server_index = down_servers_names.index(template_down_server_name)
        down_server_string = string["down_servers"][down_server_index][template_down_server_name]
        down_server_template_string = template_down_server[template_down_server_name]
        if compare_local_servers(down_server_string, down_server_template_string,
                                 template_down_server_name, statistic) is False:
            statistic.append_error("Нижний сервер " + template_down_server_name + " не корректен!", "СРАВНЕНИЕ")
            is_correct = False
            continue
    # поиск отсутвующих нижних серверов в шаблоне
    # тобиш, которые есть по факту, но нет в шаблоне
    template_down_servers_names: list = get_down_servers_names(template_string["down_servers"])
    for down_server_name in down_servers_names:
        if template_down_servers_names.count(down_server_name) == 0:
            statistic.append_warn(down_server_name + " на сервере " + main_server_ip + " в ШАБЛОНЕ!",
                                  "НЕТ НИЖНЕГО СЕРВЕРА")

    return is_correct


def get_down_servers_names(down_servers: list) -> list:
    """Функция получение ip адресов "нижних" серверов.

    :param down_servers: список всех нижних серверов
    :return: список ip адресов нижних серверов
    """
    down_servers_names: list = []
    for down_server in down_servers:
        keys = list(down_server.keys())
        down_servers_names.append(keys[0])

    return down_servers_names


def check_ptz_cams(string_cams: list, ptz_cams: list, statistic: Statistic) -> bool:
    """Функиия проверки статусов ptz у камер.

    :param string_cams: список камер из ответа;
    :param ptz_cams: список реальных ptz камер;
    :param statistic: объект класса Statistic.

    :return: флаг корректности.
    """
    is_correct = True
    for ptz_cam in ptz_cams:
        cam_index_exist = tools.get_dict_by_keys_values(string_cams, ["key2"], [ptz_cam["key2"]])
        if cam_index_exist == -1:
            statistic.append_error("'" + ptz_cam["key2"] + "'!", "НЕТ КАМЕРЫ")
            is_correct = False
            continue
        cam_index_ptz = tools.get_dict_by_keys_values(string_cams, ["key2", "ptzStat"], [ptz_cam["key2"], True])
        if cam_index_ptz == -1:
            statistic.append_error(ptz_cam["key2"] + " в ответе ws listener_pinger!", "НЕ PTZ")
            is_correct = False

    return is_correct


def listener_pinger_keys_verifier(string: dict, statistic: Statistic) -> None:
    """Функция проверка правильность ответа ws метода listener_pinger.

    :param string: значение ключа string из ответа метода
    :param statistic: объект класса Statistic
    """
    key_names: list = ['is_central_server', 'server_name', 'iv54server_port', 'rtmpPort', 'rtspPort', 'wsPort',
                       'direct_access', 'cams', 'down_servers']
    tools.check_keys_exist(string, key_names, 'string', True, statistic)
    key_values: list = [string['is_central_server'], string['server_name'], string['iv54server_port'],
                        string['rtmpPort'],
                        string['rtspPort'], string['wsPort'], string['direct_access'],
                        string['cams'],
                        string['down_servers']]
    key_types: list = [bool, str, int, int, int, int, int, list, list]
    tools.check_types(key_names, key_values, key_types, statistic)

    if string["cams"]:
        for cam in string["cams"]:
            key_names = ['key2', 'key3', 'ptzStat', 'Status']
            key_values = [cam['key2'], cam['key3'], cam['ptzStat'], cam['Status']]
            key_types = [str, str, bool, bool]
            tools.check_keys_exist(cam, key_names, 'string["cams"]', True, statistic)
            tools.check_types(key_names, key_values, key_types, statistic)

    if string["archive"]:
        for cam in string["archive"][0]:
            key_names = ['key1', 'key2', 'key3', 'is_video', 'is_audio', 'is_video_linked', 'is_audio_linked']
            tools.check_keys_exist(cam, key_names, 'string["cams"]', True, statistic)
            key_values = [cam['key1'], cam['key2'], cam['key3'], cam['is_video'], cam['is_audio'],
                          cam['is_video_linked'], cam['is_audio_linked']]
            key_types = [str, str, str, bool, bool, bool, bool]
            tools.check_types(key_names, key_values, key_types, statistic)
    else:
        statistic.append_warn("Архив пустой!", "НЕВАЛИД_ЗНАЧ")