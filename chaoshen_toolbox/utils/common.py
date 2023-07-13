import os
import subprocess
import logging

import platform
import importlib
import importlib.util
import sys
from typing import List

from chaoshen_toolbox.utils import my_decorator
from chaoshen_toolbox.config import support
from chaoshen_toolbox.config import base as base_config

LOG = logging.getLogger(__name__)


def execute_command(cmd, shell=True, encoding="utf-8") -> (bool, str):
    try:
        logging.info("execute command: %s", cmd)
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=shell)
        return True, output.decode(encoding, errors='ignore').strip()
    except subprocess.CalledProcessError as e:
        err_msg = f"cmd={cmd}, err={e.output.decode(encoding, errors='ignore').strip()}"
        LOG.error(f"execute command failed, {err_msg}")
        return False, err_msg


def check_require_pip_package(package_name, package_install_name=None):
    module = importlib.util.find_spec(package_name)
    if not module:
        package_install_name = package_install_name or package_name
        LOG.error(f"no {package_name} installed, you can use bellow install it")
        LOG.error(f"pip install {package_install_name}")
        exit(1)
    return importlib.import_module(package_name)


@my_decorator.only_run_once
def get_current_system_platform():
    """
    return linux or windows
    :return:
    """
    current_platform = platform.system().lower()
    return current_platform


def check_current_platform_is_correct(platform_name: str):
    current_platform = get_current_system_platform()
    if current_platform.lower() != platform_name.lower():
        raise Exception(f'platform is not correct, current is {current_platform}, you desired is {platform_name}')


def get_current_system_user():
    current_platform = get_current_system_platform()
    if current_platform == support.Platform.linux.name:
        return os.getlogin()
    elif current_platform == support.Platform.windows.name:
        import getpass
        return getpass.getuser()
    else:
        raise Exception(f"not support get current system user, platform={current_platform} ")


@my_decorator.only_run_once
def get_hostname():
    import socket
    return socket.gethostname()


def get_all_class_variables(class_obj):
    members = [attr for attr in dir(class_obj) if not callable(getattr(class_obj, attr)) and not attr.startswith("__")]
    return members


def get_basemodel_class_variable_names(class_obj) -> list:
    from pydantic import BaseModel
    if not issubclass(class_obj, BaseModel):
        raise Exception('123')
    return list(vars(class_obj).get('__fields__', {}).keys())


def get_home_dir():
    return os.path.expanduser('~')


def get_chaoshen_user_config_dir():
    home_dir = get_home_dir()
    user_config_dir = os.path.join(home_dir, base_config.USER_CONFIG_DIR_NAME)
    os.makedirs(user_config_dir, exist_ok=True)
    return user_config_dir


def get_python_path():
    return sys.executable


def get_current_python_share_path():
    python_path = get_python_path()
    share_path = os.path.join(python_path, '../share')
    return share_path


def get_recommended_log_path():
    platform_name = get_current_system_platform()
    if platform_name == support.Platform.linux.name:
        return f'/var/log/{base_config.PACKAGE_NAME}.log'
    elif platform_name == support.Platform.windows.name:
        return os.path.join(get_chaoshen_user_config_dir(), f"{base_config.PACKAGE_NAME}.log")
    else:
        raise Exception(f'not support platform={platform_name}')


def get_tool_platform_script_path():
    current_filepath = os.path.abspath(__file__)
    platform_name = get_current_system_platform()
    debug_platform_dir = os.path.abspath(os.path.join(current_filepath, f"../../../tools/{platform_name}"))
    installed_platform_scripts_dir = os.path.join(get_current_python_share_path(), f"tools/{platform_name}")
    if os.path.isdir(debug_platform_dir):
        return debug_platform_dir
    else:
        return os.path.abspath(installed_platform_scripts_dir)


if __name__ == '__main__':
    print(get_tool_platform_script_path())
