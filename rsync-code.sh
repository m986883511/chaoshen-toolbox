#!/bin/bash -x
# auther: wc
# filename: rsync-code.sh
#set -e
#set -u
# export RSYNC_SSH_IP=192.222.6.36;export RSYNC_SSH_PASSWORD=donotuseroot!

PROJECT_PATH=$(cd "$(dirname "$0")"; pwd -P)
printf "%-20s %-3s %-s\n" "PROJECT_PATH" "=" $PROJECT_PATH

if [ -z "${RSYNC_SSH_IP}" ]; then
    echo "ERROR: please export RSYNC_SSH_IP=ip"
    exit 1
else
    rsync_ssh_ip=${RSYNC_SSH_IP}
    if [[ ! $rsync_ssh_ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "ERROR: Usage: $rsync_ssh_ip is not ip"
        exit 1
    fi
fi
if [ -z "${RSYNC_SSH_USER}" ]; then
    rsync_ssh_user=root
else
    rsync_ssh_user=${RSYNC_SSH_USER}
fi
if [ -z "${RSYNC_SSH_PASSWORD}" ]; then
    rsync_ssh_password=donotuseroot!
else
    rsync_ssh_password=${RSYNC_SSH_PASSWORD}
fi
if [ -n "${RSYNC_EXCLUDE}" ]; then
    rsync_exclude=${RSYNC_EXCLUDE}
fi

printf "%-20s %-3s %-s\n" "rsync_ssh_ip" "=" $rsync_ssh_ip
printf "%-20s %-3s %-s\n" "rsync_ssh_user" "=" $rsync_ssh_user
printf "%-20s %-3s %-s\n" "rsync_ssh_password" "=" $rsync_ssh_password
printf "%-20s %-3s %-s\n" "rsync_exclude" "=" $rsync_exclude

function on_interrupt {
    echo -e "program is interrupted"
    exit 1
}

trap on_interrupt SIGINT

echo "wait 10 seconds or press enter to continue："

read -t 10 -n 1 input

if [ -z "$input" ]; then
    echo "auto confirm"
else
    echo "you confirm"
fi

sshpass -p $rsync_ssh_password ssh -o 'StrictHostKeyChecking no' $rsync_ssh_user@$rsync_ssh_ip "mkdir -p /root/rsync"
if [[ $? -ne 0 ]];then
    echo "ERROR: mkdir -p /root/rsync failed"
    exit 1
fi

if [ -n "${rsync_exclude}" ]; then
    rsync -avz -e "sshpass -p $rsync_ssh_password ssh -o 'StrictHostKeyChecking no'" --exclude $rsync_exclude $PROJECT_PATH $rsync_ssh_user@$rsync_ssh_ip:/root/rsync
else
    rsync -avz -e "sshpass -p $rsync_ssh_password ssh -o 'StrictHostKeyChecking no'" $PROJECT_PATH $rsync_ssh_user@$rsync_ssh_ip:/root/rsync
fi
if [[ $? -ne 0 ]];then
    echo "ERROR: rsync -avz -e sshpass -p $rsync_ssh_password ssh -o 'StrictHostKeyChecking no' --exclude $rsync_exclude $PROJECT_PATH $rsync_ssh_user@$rsync_ssh_ip:/root/rsync failed"
    exit 1
fi