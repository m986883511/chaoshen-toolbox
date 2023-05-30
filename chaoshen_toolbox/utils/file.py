
import os


def add_suffix_to_file(filepath, suffix):
    # 拆分文件路径和文件名
    filepath = os.path.abspath(filepath)
    dirname, filename = os.path.split(filepath)

    # 拆分文件名和后缀
    basename, extension = os.path.splitext(filename)

    # 添加后缀
    new_basename = f"{basename}-{suffix}"

    # 重组文件名和后缀
    new_filename = f"{new_basename}{extension}"

    # 重组文件路径和文件名
    new_filepath = os.path.join(dirname, new_filename)

    return new_filepath

