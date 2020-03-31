import os
import time
import json
import hashlib
import sqlite3

from lib.log_and_statistic import log
from lib.log_and_statistic.statistics import Statistic

from scripts.common import tools


def json_float_parser(string: str) -> float:
    """Функция парсинга json строки для десериализации.

    :param string:
    :return:
    """
    format_s = '{:20.20}'.format(string)
    float_format_s = float(format_s)
    return float_format_s


def get_full_json_graph_by_cam(path_to_db: str, key1: str, key2: str, key3: str, statistic: Statistic) -> dict:
    """Получение json графа (камеры) из БД.

    Делает SELECT запрос к БД на получение json-ов всех камер и профилей, а затем осуществляется
    поиск нужной камеры.
    :param path_to_db: путь к файлу БД
    :param key1: имя сервера
    :param key2: имя камеры
    :param key3: профиль камеры
    :param statistic: объект класса Statistic
    :return: json в виде словаря
    """
    logger = log.get_logger("scripts/common/db")
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
            statistic.append_error("Камера '" + db_setname + "' отсутствует!", "БД", False)
            return {}

        logger.info("db select json by '" + db_setname + "' cam was executed successfully!")
        log.print_all("Получение json из БД камеры '" + db_setname + "' выполнено успешно!")
        return json.loads(json_cam[0][0], parse_float=json_float_parser)
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
    logger = log.get_logger("scripts/common/db")
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


def update_full_json_graph_by_cam(path_to_db: str, key1: str, key2: str, key3: str, json_cam: dict,
                                  statistic: Statistic) -> int:
    """Изменение json указанной камеры в БД.

    :param path_to_db:
    :param key1: имя сервера
    :param key2: имя камеры
    :param key3: профиль камеры
    :param json_cam: json (граф) камеры
    :param statistic: объект класса Statistic
    :return: код ошибки: 0 - все ок.
    """
    logger = log.get_logger("scripts/common/db")
    logger.info("call func update_full_json_graph_by_cam(path_to_db, key1, key2, key3, dict_json_graph)")
    logger.debug("update_full_json_graph_by_cam(" + path_to_db + ", " + key1 + ", " + key2 + ", " + key3 + ", "
                 + str(json_cam) + ")")

    if not os.path.exists(path_to_db):
        statistic.append_error("Файла БД не существует!", "БД", True)

    try:
        time.sleep(0.2)
        conn = sqlite3.connect(path_to_db)
        cursor = conn.cursor()
        db_setname = key1 + "_" + key2 + "_" + key3
        db_setvalue = json.dumps(json_cam)
        db_setvalue = db_setvalue.replace("/$", "\\/$")

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
            log.print_all("Камера '" + db_setname + "' уже имеет такой json!")
            return 0

        time.sleep(0.2)
        sql_cmd = "UPDATE setting SET setvalue = ?, sethash = ? WHERE setid = ?"
        cursor.execute(sql_cmd, [db_setvalue, db_sethash_new, str(db_setid)])
        conn.commit()

        conn.close()
        logger.info("db update json for '" + key2 + "' cam was executed successfully")
        log.print_all("Обновление json камеры '" + db_setname + "' выполнено успешно!")
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


def get_lists_key2_and_id54(path_to_db: str, key1: str, statistic: Statistic) -> tuple:
    """Получение списка занятых id54 на ВСЕХ серверах и key2 на УКАЗАННОМ сервере камер

    :param path_to_db: путь к бд
    :param key1: имя сервера
    :param statistic: объект класса Statistic

    :return:  tuple: 0 - список key2; 1 - список id54
    """

    if not os.path.exists(path_to_db):
        statistic.append_error("Файла БД не существует!", "БД", True)

    try:
        time.sleep(0.2)
        conn = sqlite3.connect(path_to_db)
        cursor = conn.cursor()

        sql_cmd = "SELECT setvalue FROM setting WHERE settypeid = ?"
        cursor.execute(sql_cmd, [1])
        jsons_cams: list = cursor.fetchall()

        conn.commit()
        conn.close()
    except sqlite3.OptimizedUnicode:
        statistic.append_error("Ошибка выполнения команды!", "БД", True)

    list_id54: list = []
    list_key2: list = []
    for json_cam in jsons_cams:
        json_cam: dict = json.loads(json_cam[0])

        # добавляем в список занятый key2
        tools.check_keys_exist(json_cam, ['common'], 'json_cam', True, statistic)
        tools.check_keys_exist(json_cam['common'], ['key1', 'key2', 'key3'], 'json_cam["common"]', True, statistic)
        to_add = True
        for key2 in list_key2:
            if key2 == json_cam['common']['key2']:
                to_add = False
                break
        if to_add and json_cam['common']['key1'] == key1:
            list_key2.append(json_cam['common']['key2'])

        # добавляем в список занятый id54
        tools.check_keys_exist(json_cam, ['network_5_4'], 'json_cam', True, statistic)
        tools.check_types(['network_5_4'], [json_cam['network_5_4']], [list], statistic)
        tools.check_values(['network_5_4'], [json_cam['network_5_4']], [0], [">"], statistic)

        tools.check_keys_exist(json_cam['network_5_4'][0], ['iv54server'], 'json_cam["network_5_4"][0]', True, statistic)
        tools.check_keys_exist(json_cam['network_5_4'][0]['iv54server'], ['ID_54'],
                               'json_cam["network_5_4"][0]["iv54server"]', True, statistic)
        tools.check_keys_exist(json_cam['network_5_4'][0]['iv54server']['ID_54'], ['_value'],
                               'json_cam["network_5_4"][0]["iv54server"]["ID_54"]', True, statistic)
        to_add = True
        for id54 in list_id54:
            if id54 == json_cam['network_5_4'][0]['iv54server']['ID_54']["_value"]:
                to_add = False
                break
        if to_add:
            list_id54.append(json_cam['network_5_4'][0]['iv54server']['ID_54']["_value"])

    if not list_key2:
        statistic.append_error("on server '" + key1 + "'!", "NO_CAMS", False)

    return list_key2, list_id54


def get_list_key1(path_to_db: str, statistic: Statistic):
    """Получение списка всех серверов из БД.

    :param path_to_db: путь к бд
    :param statistic: объект класса Statistic
    :return:
    """
    logger = log.get_logger("scripts/common/db")
    logger.info("was called (path_to_db: str, statistic: Statistic)")
    logger.debug("with params (" + path_to_db + ")")

    if not os.path.exists(path_to_db):
        statistic.append_error("Файла БД не существует!", "БД", True)

    try:
        time.sleep(0.2)
        conn = sqlite3.connect(path_to_db)
        cursor = conn.cursor()

        sql_cmd = "SELECT vsrname FROM videoserver"
        cursor.execute(sql_cmd)
        query_result = cursor.fetchall()

        conn.commit()
        conn.close()

        servers = []
        for result in query_result:
            servers.append(result[0])

        if not servers == 0:
            statistic.append_error("Нет ни одного сервера!", "БД", True)

        return servers
    except sqlite3.OptimizedUnicode:
        statistic.append_error("Ошибка выполнения команды!", "БД", True)
