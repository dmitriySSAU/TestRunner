import os
import time
import json
import hashlib
import sqlite3

from typing import Tuple

from lib.log_and_statistic import log
from lib.log_and_statistic.statistic import Statistic

from scripts.common import tools


def json_float_parser(string: str) -> float:
    """Функция парсинга типа float в json при десериализации.
    Необходима для избавления от экспоненты при десириализации, которая автоматически
    добавляется библиотекой json.

    :param string: строка с float.

    :return: отформатированный float без экспоненты.
    """
    format_s = '{:20.20}'.format(string)
    float_format_s = float(format_s)
    return float_format_s


def get_cam_json(path_to_db: str, key1: str, key2: str, key3: str, statistic: Statistic) -> dict:
    """Получение json графа (камеры) из БД.

    Делает SELECT запрос к БД на получение json-ов всех камер и профилей, а затем осуществляется
    поиск нужной камеры.
    :param path_to_db: путь к файлу БД;
    :param key1: имя сервера;
    :param key2: имя камеры;
    :param key3: профиль камеры;
    :param statistic: объект класса Statistic.

    :return: json в виде словаря.
    """
    logger = statistic.get_log().get_logger("scripts/common/db")
    logger.info("was called path_to_db: str, key1: str, key2: str, key3: str, statistic: Statistic)")
    logger.debug("with params (" + path_to_db + ", " + key1 + ", " + key2 + ", " + key3 + ")")

    if not os.path.exists(path_to_db):
        statistic.append_error("Файла БД не существует!", "БД", True)
    try:
        time.sleep(0.2)
        conn = sqlite3.connect(path_to_db)
        cursor = conn.cursor()
        db_setname = key1 + "_" + key2 + "_" + key3
        sql_cmd = 'SELECT setvalue FROM setting WHERE settypeid = ? AND setname = ?'
        cursor.execute(sql_cmd, [1, db_setname])
        json_cam = cursor.fetchall()
        conn.commit()
        conn.close()

        if not json_cam:
            statistic.append_error("Камера '" + db_setname + "' отсутствует!", "БД")
            return {}

        logger.info("db select json by '" + db_setname + "' cam was executed successfully!")
        statistic.append_info("Получение json из БД камеры '" + db_setname + "' выполнено успешно!", "БД")
        # в некоторых плагинах есть сочетания слешей вида: \/, которое нельзя никак заменять.
        # При десериализации по умолчанию символ \ пропадает, как служебный.
        # Поэтому перед десериализацией необходимо добавить два слеша, чтобы было так (\\/).
        # Однако почему то в таком случае после десериализации оно так и останется (\\/), а не (\/).
        # То есть потом при сериализации этот момент нужно учесть и заменить на \/.
        replaced_json_cam = json_cam[0][0].replace("\\/", "\\\\/")
        return json.loads(replaced_json_cam, parse_float=json_float_parser)
    except sqlite3.OptimizedUnicode:
        statistic.append_error("Ошибка выполнения команды!", "БД", True)


def update_setname_by_cam(path_to_db: str, key1: str, key2: str, key3: str, new_key1: str, new_key2: str,
                          new_key3: str, statistic: Statistic) -> int:
    """Функция изменения имени камеры в БД.

    :param path_to_db:
    :param key1: имя сервера
    :param key2: имя камеры
    :param key3: профиль камеры
    :param new_key1: новое имя сервера
    :param new_key2: новое имя камеры
    :param new_key3: новый профиль
    :param statistic: объект класса Statistic
    :return: код ошибки: 0 - все ок.
    """
    logger = statistic.get_log().get_logger("scripts/common/db")
    logger.info("was called (path_to_db: str, key1: str, key2: str, key3: str, new_key1: str, new_key2: str," +
                "new_key3: str, statistic: Statistic)")
    logger.debug("with params (" + path_to_db + ", " + key1 + ", " + key2 + ", " + key3 + ", " + new_key1 + ", "
                 + new_key2 + ", " + new_key3 + ")")

    if not os.path.exists(path_to_db):
        statistic.append_error("Файла БД не существует!", "БД", True)

    try:
        time.sleep(0.2)
        conn = sqlite3.connect(path_to_db)
        cursor = conn.cursor()
        db_setname = key1 + "_" + key2 + "_" + key3
        db_new_setname = new_key1 + "_" + new_key2 + "_" + new_key3

        sql_cmd = "SELECT setid FROM setting WHERE settypeid = ? AND setname = ?"
        cursor.execute(sql_cmd, [1, db_setname])
        db_setid = cursor.fetchall()[0][0]

        time.sleep(0.2)
        sql_cmd = "UPDATE setting SET setname = ? WHERE setid = ?"
        cursor.execute(sql_cmd, [db_new_setname, str(db_setid)])
        conn.commit()

        conn.close()
        logger.info("db update setname for '" + key2 + "' cam was executed successfully")
        log.print_all("Обновление имени камеры c '" + db_setname + "' на '" + db_new_setname + "' выполнено успешно!")
        return 0
    except sqlite3.OptimizedUnicode:
        statistic.append_error("Ошибка выполнения команды!", "БД", True)


def update_cam_json(db_path: str, key1: str, key2: str, key3: str, cam_json: dict, statistic: Statistic) -> int:
    """Изменение json указанной камеры в БД.

    :param db_path: путь к БД;
    :param key1: имя сервера;
    :param key2: имя камеры;
    :param key3: профиль камеры;
    :param cam_json: json (граф) камеры;
    :param statistic: объект класса Statistic.

    :return: код ошибки: 0 - все ок.
    """
    logger = statistic.get_log().get_logger("scripts/common/db")
    logger.info("was called (db_path: str, key1: str, key2: str, key3: str, cam_json: dict, statistic: Statistic)")
    logger.debug("with params (" + db_path + ", " + key1 + ", " + key2 + ", " + key3 + ", " + str(cam_json) +
                 ", stat_obj)")

    if not os.path.exists(db_path):
        statistic.append_error("Файла БД не существует!", "БД", True)

    try:
        time.sleep(0.2)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        db_setname = key1 + "_" + key2 + "_" + key3
        db_setvalue = json.dumps(cam_json, indent="\t", ensure_ascii=False)
        # Учитывается момент с \\/ и заменяется на \/.
        db_setvalue = db_setvalue.replace("\\\\/", "\\/")

        sql_cmd = "SELECT setid FROM setting WHERE settypeid = ? AND setname = ?"
        cursor.execute(sql_cmd, [1, db_setname])
        db_setid = cursor.fetchall()[0][0]

        time.sleep(0.2)
        sql_cmd = "SELECT sethash FROM setting WHERE setid = ?"
        cursor.execute(sql_cmd, [str(db_setid)])
        db_sethash = cursor.fetchall()[0][0]
        obj_md5_hash = hashlib.md5(db_setvalue.encode('utf-8'))
        db_sethash_new = obj_md5_hash.hexdigest()
        if db_sethash == db_sethash_new:
            conn.close()
            logger.info("cam '" + key2 + "' on server '" + key1 + "' already has the same json!")
            statistic.append_info("Камера '" + db_setname + "' уже имеет такой json!", "БД")
            return 0

        time.sleep(0.2)
        sql_cmd = "UPDATE setting SET setvalue = ?, sethash = ? WHERE setid = ?"
        cursor.execute(sql_cmd, [db_setvalue, db_sethash_new, str(db_setid)])
        conn.commit()

        conn.close()
        logger.info("db update json for '" + key2 + "' cam was executed successfully")
        statistic.append_info("Обновление json камеры '" + db_setname + "' выполнено успешно!", "БД")
        return 0
    except sqlite3.OptimizedUnicode:
        statistic.append_error("Ошибка выполнения команды!", "БД", True)


def insert_new_cam(path_to_db: str, key1: str, key2: str, key3: str, json_graph: dict, statistic: Statistic) -> int:
    """Вставка нового графа (камеры) в таблицу

    :param path_to_db: путь до БД
    :param key1: имя сервера
    :param key2: имя камеры
    :param key3: профиль
    :param json_graph: граф в формате json
    :param statistic: объект класса Statistic
    :return: первичный ключ
    """

    if not os.path.exists(path_to_db):
        statistic.append_error("Файла БД не существует!", "БД", True)

    try:
        time.sleep(0.5)
        conn = sqlite3.connect(path_to_db)
        cursor = conn.cursor()
        db_setname = key1 + "_" + key2 + "_" + key3
        db_setvalue = json.dumps(json_graph).replace("\\\\/$", "\\/$")

        obj_md5_hash = hashlib.md5(db_setvalue.encode('utf-8'))
        db_sethash = obj_md5_hash.hexdigest()

        sql_cmd = "INSERT INTO setting (setid, settypeid, setname, setvalue, setcomment, setinfo, sethash) " \
                  "VALUES (?, ?, ?, ?, ?, ?, ?)"
        cursor.execute(sql_cmd, [None, 1, db_setname, db_setvalue, "", "", db_sethash])
        conn.commit()
        time.sleep(0.5)
        db_setid = get_setid(path_to_db, key1, key2, key3, statistic)

        conn.close()
        return db_setid
    except sqlite3.OptimizedUnicode:
        statistic.append_error("Ошибка выполнения команды!", "БД", True)


def get_setid(path_to_db: str, key1: str, key2: str, key3: str, statistic: Statistic) -> int:
    """Получить первичный ключ камеры (поле setid) по ее полному имени.

    :param path_to_db: путь до БД
    :param key1: имя сервера
    :param key2: имя камеры
    :param key3: профиль
    :param statistic: объект класса Statistic
    :return: первичный ключ камеры
    """

    if not os.path.exists(path_to_db):
        statistic.append_error("Файла БД не существует!", "БД", True)

    try:
        time.sleep(0.2)
        conn = sqlite3.connect(path_to_db)
        cursor = conn.cursor()
        db_setname = key1 + "_" + key2 + "_" + key3

        sql_cmd = "SELECT setid FROM setting WHERE settypeid = ? AND setname = ?"
        cursor.execute(sql_cmd, [1, db_setname])
        db_setid = cursor.fetchall()[0][0]

        conn.close()
        return db_setid
    except sqlite3.OptimizedUnicode:
        statistic.append_error("Ошибка выполнения команды!", "БД", True)


def delete_cam(path_to_db: str, key1: str, key2: str, key3: str, statistic: Statistic) -> int:
    """Функция удаления камеры из БД.

    :param path_to_db: путь до БД
    :param key1: имя сервера
    :param key2: имя камеры
    :param key3: профиль
    :param statistic: объект класса Statistic
    :return: код ошибки: 0 - все ок.
    """

    if not os.path.exists(path_to_db):
        statistic.append_error("Файла БД не существует!", "БД", True)

    try:
        time.sleep(0.2)
        conn = sqlite3.connect(path_to_db)
        cursor = conn.cursor()
        db_setname = key1 + "_" + key2 + "_" + key3

        sql_cmd = "SELECT setid FROM setting WHERE settypeid = ? AND setname = ?"
        cursor.execute(sql_cmd, [1, db_setname])
        db_setid = cursor.fetchall()[0][0]

        time.sleep(0.2)
        sql_cmd = "DELETE FROM setting WHERE setid = ?"

        cursor.execute(sql_cmd, [str(db_setid)])
        conn.commit()

        conn.close()
        return 0
    except sqlite3.OptimizedUnicode:
        statistic.append_error("Ошибка выполнения команды!", "БД", True)


def get_cams_names(db_path: str, server: str, statistic: Statistic) -> tuple:
    """Получение списка имен камер с указанного сервера.

    :param db_path: путь к бд;
    :param server: имя сервера;
    :param statistic: объект класса Statistic.

    :return: список имен камер с конкретного сервера.
    """

    if not os.path.exists(db_path):
        statistic.append_error("Файла БД не существует!", "БД", True)

    full_names = []
    try:
        time.sleep(0.2)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        sql_cmd = "SELECT setname FROM setting WHERE settypeid = ? AND setname LIKE ?"
        cursor.execute(sql_cmd, [1, server + "%"])
        full_names: list = cursor.fetchall()

        conn.commit()
        conn.close()
    except sqlite3.OptimizedUnicode:
        statistic.append_error("Ошибка выполнения команды!", "БД", True)

    if not full_names:
        statistic.append_warn("Сервер: " + server + "!", "НЕТ_КАМЕР")

    cams_names: list = []
    for full_name in full_names:
        first_index_ = full_name[0].find("_")
        last_index_ = full_name[0].rfind("_")
        new_cam_name = full_name[0][first_index_ + 1: last_index_]

        # из-за разных профилей по одной камере могут быть одинаковые имена,
        # а дублирование имен не нужно.
        add = True
        for cam_name in cams_names:
            if new_cam_name == cam_name:
                add = False
                break
        if add:
            cams_names.append(new_cam_name)

    return tuple(cams_names)


def get_cams_id(db_path: str, statistic: Statistic) -> tuple:
    if not os.path.exists(db_path):
        statistic.append_error("Файла БД не существует!", "БД", True)

    cam_jsons = []
    try:
        time.sleep(0.2)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        sql_cmd = "SELECT setvalue FROM setting WHERE settypeid = ?"
        cursor.execute(sql_cmd, [1])
        cam_jsons: list = cursor.fetchall()

        conn.commit()
        conn.close()
    except sqlite3.OptimizedUnicode:
        statistic.append_error("Ошибка выполнения команды!", "БД", True)

    list_id54 = []
    for cam_json in cam_jsons:
        cam_json = json.loads(cam_json[0])
        if tools.check_keys_exist(cam_json, ['network_5_4'], 'cam_json', False, statistic) is False:
            continue
        tools.check_types(['network_5_4'], [cam_json['network_5_4']], [list], statistic)

        if not cam_json['network_5_4']:
            continue
        if tools.check_keys_exist(cam_json['network_5_4'][0], ['iv54server'], 'cam_json["network_5_4"][0]', False,
                                  statistic) is False:
            continue
        if tools.check_keys_exist(cam_json['network_5_4'][0]['iv54server'], ['ID_54'],
                                  'cam_json["network_5_4"][0]["iv54server"]', False, statistic) is False:
            continue
        if tools.check_keys_exist(cam_json['network_5_4'][0]['iv54server']['ID_54'], ['_value'],
                                  'cam_json["network_5_4"][0]["iv54server"]["ID_54"]', False, statistic) is False:
            continue
        to_add = True
        for id54 in list_id54:
            if id54 == cam_json['network_5_4'][0]['iv54server']['ID_54']["_value"]:
                to_add = False
                break
        if to_add:
            list_id54.append(cam_json['network_5_4'][0]['iv54server']['ID_54']["_value"])

    return tuple(list_id54)


def get_servers(db_path: str, statistic: Statistic) -> Tuple[str]:
    """Получение списка всех серверов из БД.

    :param db_path: путь к бд;
    :param statistic: объект класса Statistic.

    :return: список серверов.
    """
    logger = statistic.get_log().get_logger("scripts/common/db")
    logger.info("was called (path_to_db: str, statistic: Statistic)")
    logger.debug("with params (" + db_path + ")")

    if not os.path.exists(db_path):
        statistic.append_error("Файла БД не существует!", "БД", True)
    try:
        time.sleep(0.2)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        sql_cmd = "SELECT vsrname FROM videoserver"
        cursor.execute(sql_cmd)
        query_result = cursor.fetchall()
        conn.commit()
        conn.close()

        servers = []
        for result in query_result:
            servers.append(result[0])
        if not servers:
            statistic.append_error("Не обнаружено ни одного сервера!", "БД")
        return tuple(servers)
    except sqlite3.OptimizedUnicode:
        statistic.append_error("Ошибка выполнения команды!", "БД", True)
