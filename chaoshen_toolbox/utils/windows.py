import pyuac

from chaoshen_toolbox.utils import common
from chaoshen_toolbox.model import network as network_model


def main():
    print("Do stuff here that requires being run as an admin.")
    # The window will disappear as soon as the program exits!
    input("Press enter to close the window. >")


def run_as_admin():
    if not pyuac.isUserAdmin():
        print("Re-launching as admin!")
        pyuac.runAsAdmin()


class Netsh:
    @staticmethod
    def config_ip_command(n_c: network_model.NetshConfigIpModel):
        commands = [f"netsh interface ipv4 set address name={n_c.nic} static {n_c.ip} {n_c.mask} {n_c.route}"]
        return commands

    @staticmethod
    def config_dns_command(n_c: network_model.NetshConfigIpModel):
        commands = []

        dnss = [n_c.dns] if not isinstance(n_c.dns, list) else n_c.dns

        for i, dns in enumerate(dnss):
            set_or_add = 'set' if i == 0 else 'add'
            commands.append(f"netsh interface ip {set_or_add} dns name={n_c.nic} static {n_c.dns} validate=no")
        return commands

    @staticmethod
    def enable_wlan_interface_command(wlan_nic_name):
        commands = [f"netsh interface set interface {wlan_nic_name} enabled"]
        return commands


def get_available_wifi_names():
    cmd = "netsh wlan show networks"
    success, output = common.execute_command(cmd)
    temp_str = output.split('\r\n')
    new_temp_str = [i.strip() for i in temp_str if 'ssid' in i.lower()]
    wifi_names = []
    for i in new_temp_str:
        if not isinstance(i, str):
            continue
        if not i.lower().startswith('ssid'):
            continue
        if ':' not in i:
            continue
        if not i.split(' ')[1].isdigit():
            continue
        location = i.find(":")
        wifi_name = i[location + 1:].strip()
        if not wifi_name:
            continue
        wifi_names.append(wifi_name)
    return wifi_names


if __name__ == "__main__":
    if not pyuac.isUserAdmin():
        print("Re-launching as admin!")
        # pyuac.runAsAdmin()

    from pprint import pprint

    pprint(get_available_wifi_names())  # Already an admin here.
