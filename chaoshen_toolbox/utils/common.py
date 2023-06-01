import subprocess
import logging
import importlib
import importlib.util

LOG = logging.getLogger(__name__)


def execute_command(cmd, shell=True) -> (bool, str):
    try:
        logging.info("execute command: %s", cmd)
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=shell)
        return True, output.decode().strip()
    except subprocess.CalledProcessError as e:
        LOG.error("execute failed, error message: %s", e.output.decode().strip())
        return False, e.output.decode().strip()


def check_require_pip_package(package_name, package_install_name=None):
    module = importlib.util.find_spec(package_name)
    if not module:
        package_install_name = package_install_name or package_name
        LOG.error(f"no {package_name} installed, you can use bellow install it")
        LOG.error(f"pip install {package_install_name}")
        exit(1)
    return importlib.import_module(package_name)
