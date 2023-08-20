#!/bin/bash
all_uuid=$(nmcli -g UUID connection show)

for uuid in $all_uuid
do
    nmcli connection delete uuid "$uuid"
done

nmcli connection add type ethernet con-name manage ifname eth0 ipv4.addr 192.222.1.101/20 ipv4.gateway 192.222.1.254 ipv4.dns 8.8.8.8 ipv4.method manual
systemctl restart NetworkManager
