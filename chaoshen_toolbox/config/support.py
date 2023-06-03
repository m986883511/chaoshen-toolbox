from enum import Enum


class Platform(Enum):
    windows = ['win7', 'win10']
    linux = ['fedora']


config_ip_support_platform = [Platform.windows.name, Platform.linux.name]

