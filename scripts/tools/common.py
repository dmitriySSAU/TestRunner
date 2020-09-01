import os
import time
import filecmp

from lib.log_and_statistic.statistic import Statistic


def compare_dirs(dir1: str, dir2: str, statistic: Statistic) -> None:
    """Сравнение двух директорий
    Рекурсивное сравнение двух директорий.
    Два файла равны, если их имена и содержимое одинаковы.

    :param dir1: Путь к первой директории;
    :param dir2: Путь к второй директории;
    :param statistic: объект класса Statistic.
   """
    slash_index = dir1.rfind("/")
    simple_dir1_name = dir1[slash_index + 1:]
    slash_index = dir2.rfind("/")
    simple_dir2_name = dir2[slash_index + 1:]
    dirs_cmp = filecmp.dircmp(dir1, dir2)  # сравнение директорий по количеству файлов и поддиректориям
    if len(dirs_cmp.left_only) > 0:
        message = "\nПапки только в " + simple_dir1_name + "\n" + str(dirs_cmp.left_only) + "\n"
        statistic.append_error(message, "ОТЛИЧИЕ")
        # print("Папки и файлы, содержащиеся только в пути ", dir1, dirs_cmp.left_only)
    if len(dirs_cmp.right_only) > 0:
        message = "\nПапки только в " + simple_dir2_name + "\n" + str(dirs_cmp.right_only) + "\n"
        statistic.append_error(message, "ОТЛИЧИЕ")
    (_, mismatch, errors) = filecmp.cmpfiles(dir1, dir2, dirs_cmp.common_files,
                                             shallow=False)  # непосредственное сравнение файлов
    if len(mismatch) > 0:
        for file in mismatch:
            if os.stat(dir1 + "/" + file).st_mtime > os.stat(dir2 + "/" + file).st_mtime :
                first_dir_date = " (новее)"
                second_dir_date = ""
            else:
                first_dir_date = ""
                second_dir_date = " (новее)"

            first_file_info = "\nИмя: /" + simple_dir1_name + "/" + file + "\n" + \
                              "Размер: " + str(os.stat(dir1 + "/" + file).st_size) + " Б" + "\n" + \
                              "Дата изменения: " + time.strftime("%Y-%m-%d %H:%M:%S",
                                                                 time.localtime(os.stat(dir1 + "/" + file).st_mtime)) + first_dir_date
            second_file_info = "Имя: /" + simple_dir2_name + "/" + file + "\n" + \
                               "Размер: " + str(os.stat(dir2 + "/" + file).st_size) + " Б" + "\n" + \
                               "Дата изменения: " + time.strftime("%Y-%m-%d %H:%M:%S",
                                                                  time.localtime(os.stat(dir2 + "/" + file).st_mtime)) + second_dir_date + "\n"
            message = first_file_info + "\n------------------------------------\n" + second_file_info
            message = message.replace("\\", "/")
            statistic.append_error(message, "ОТЛИЧИЕ")
    if len(errors) > 0:
        statistic.append_error("Ошибка доступа к файлам: " + errors, "КРИТ", True)

    # рекурсивный переход по общим поддиректориям
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        compare_dirs(new_dir1, new_dir2, statistic)
