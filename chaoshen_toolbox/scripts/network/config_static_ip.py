import argparse
import os
import logging
import shutil
from typing import Dict, List
from pprint import pprint

from chaoshen_toolbox.utils import file, common, windows
from chaoshen_toolbox.model import network
from chaoshen_toolbox.config.base import PACKAGE_SHARE_DIR_NAME
from chaoshen_toolbox import LOG

config_file_name = 'network.yaml'
current_dir = os.path.dirname(__file__)
debug_config_path = os.path.abspath(os.path.join(current_dir, f'../../../user_config/{config_file_name}'))
default_config_path = os.path.abspath(os.path.join(common.get_current_python_share_path(),
                                                   f'{PACKAGE_SHARE_DIR_NAME}/default_config/{config_file_name}'))
user_config_path = os.path.abspath(os.path.join(common.get_chaoshen_user_config_dir(), config_file_name))

psutil_module = common.check_require_pip_package("psutil", package_install_name="psutil")

route_choices = common.get_basemodel_class_variable_names(network._UserConfigNetworkModel.muti_route)
interface_choices = common.get_basemodel_class_variable_names(network._UserConfigNetworkModel.muti_nic)

generated_config_network_command = []
available_wifi_names = []


def get_network_config() -> Dict[str, network.UserConfigNetworkFileModel]:
    if os.path.exists(debug_config_path):
        LOG.info(f"in debug mode, use config_path={debug_config_path}")
        network_config = file.read_yaml(debug_config_path)
    else:
        LOG.info(f"not in debug mode, try to find config_file")
        if not os.path.exists(default_config_path):
            raise Exception(f"not find default network config, config_path={default_config_path}")
        default_config = file.read_yaml(default_config_path)
        if not os.path.exists(user_config_path):
            LOG.info('not exist user network config, copy it from default')
            shutil.copy(default_config_path, user_config_path)
        user_config = file.read_yaml(user_config_path)
        default_config.update(user_config)
        network_config = default_config
        LOG.debug(f"summary network config is {network_config}")
    network_config = {key: network.UserConfigNetworkFileModel(**value) for key, value in network_config.items()}
    return network_config


def prepare_nic(interface) -> str:
    import psutil
    global generated_config_network_command
    current_network_status = psutil.net_if_stats()
    # pprint(current_network_status)
    nic_status = {}
    wlan_nic_names = []

    for nic_name, obj in current_network_status.items():
        nic_status[nic_name] = obj.isup
        if 'wlan' in nic_name.lower():
            wlan_nic_names.append(nic_name)

    if interface == interface_choices[0]:
        if not wlan_nic_names:
            raise Exception(f'not find wlan nic, all nic is {nic_status.keys()}')
        if len(wlan_nic_names) > 1:
            raise Exception(f'should not find multi wlan nic, they are {wlan_nic_names}')
        wlan_nic_name = wlan_nic_names[0]
        if not nic_status[wlan_nic_name]:
            commands = windows.Netsh.enable_wlan_interface_command(wlan_nic_name)

            generated_config_network_command += commands
            execute_command(f"enable {wlan_nic_name} or not")

        return wlan_nic_name

    else:
        if interface not in nic_status:
            raise Exception(f'not find interface named {interface}, all nic is {nic_status.keys()}')
        else:
            if not nic_status[interface]:
                commands = windows.Netsh.enable_wlan_interface_command(interface)
                generated_config_network_command += commands
            return interface


def execute_command(promot):
    if generated_config_network_command:
        LOG.info(promot)
        result = input(promot)

    for i in range(len(generated_config_network_command)):
        cmd = generated_config_network_command.pop()
        LOG.info(f'execute command {cmd}')
        os.system(cmd)


def get_config_ip_command(route, interface, place):
    platform_name = common.get_current_system_platform()
    hostname = common.get_hostname()
    user_config = get_network_config()

    interface_nic = prepare_nic(interface)
    global available_wifi_names
    available_wifi_names = windows.get_available_wifi_names()
    LOG.info(f'available_wifi_names is {available_wifi_names}')

    # get_network_scripts_path = os.path.join(common.get_tool_platform_script_path(), 'Get-NetIpConfigration.ps1')
    # success, result = common.execute_command(f"powershell {get_network_scripts_path}")
    # if not success:
    #     raise Exception(f'get {platform_name} network config failed')
    # LOG.info(result)

    # common.execute_command("")

    if hostname in user_config:
        network_config = user_config[hostname]
        assert platform_name == network_config.platform, \
            f"check {hostname} platform not equal to config={network_config}"
        for where, value in network_config.network.items():

            # dns = value.dns
            if not set(value.wifi) - set(available_wifi_names):
                continue
            for i in available_wifi_names:
                if i in value.wifi:
                    LOG.info(f'find wifi {i}, so you are in {where}')
                    break
            else:
                LOG.info(f'not in {where}, check another')
                continue
            LOG.info(f"{where} config is {value.dict()}")
            config = {
                "ip": value.nic.wireless.split('/')[0],
                "mask": "255.255.255.0",
                "dns": "8.8.8.8",
                "route": getattr(value.route, route),
                "nic": interface_nic

            }

            config = network.NetshConfigIpModel(**config)
            global generated_config_network_command
            commands = windows.Netsh.config_ip_command(config)

            generated_config_network_command += commands
            commands = windows.Netsh.config_dns_command(config)
            generated_config_network_command += commands
            execute_command("config_ip")
            break



    else:
        err_msg = f"not find you device_name={hostname} in config={user_config_path}"
        LOG.error(err_msg)
        raise Exception(err_msg)


def main():
    parser = argparse.ArgumentParser(description='output config static ip command')

    parser.add_argument('-r', '--route',
                        choices=route_choices,
                        default=route_choices[0],
                        help='config route ip')
    parser.add_argument('-i', '--interface',
                        choices=interface_choices,
                        default=interface_choices[0],
                        help='default is wireless, auto find wlan interface')
    parser.add_argument('-p', '--place',
                        help='where place')
    args = parser.parse_args()

    LOG.info(f"{__file__} execute with args={args.__dict__}")
    windows.run_as_admin()
    get_config_ip_command(
        route=args.route,
        interface=args.interface,
        place=args.place
    )


if __name__ == '__main__':
    main()
