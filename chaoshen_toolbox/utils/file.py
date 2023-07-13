import os
import yaml
import configparser


def add_suffix_to_file(filepath, suffix, connector='-'):
    # 拆分文件路径和文件名
    filepath = os.path.abspath(filepath)
    dirname, filename = os.path.split(filepath)

    # 拆分文件名和后缀
    basename, extension = os.path.splitext(filename)

    # 添加后缀
    new_basename = f"{basename}{connector}{suffix}"

    # 重组文件名和后缀
    new_filename = f"{new_basename}{extension}"

    # 重组文件路径和文件名
    new_filepath = os.path.join(dirname, new_filename)

    return new_filepath


def read_yaml(filepath) -> dict:
    with open(filepath, 'r') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    return data


def read_ini(filepath) -> dict:
    config = configparser.ConfigParser()
    config.read(filepath)
    return config


def ini_to_dict(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)

    ini_dict = {}
    for section in config.sections():
        ini_dict[section] = {}
        for option in config.options(section):
            value = config.get(section, option)
            ini_dict[section][option] = value
    return ini_dict
