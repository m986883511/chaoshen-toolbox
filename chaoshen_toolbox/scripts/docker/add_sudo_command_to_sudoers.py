import argparse
import os
import logging

from chaoshen_toolbox.utils import linux
from chaoshen_toolbox.utils import common

from chaoshen_toolbox import LOG

SUDO_COMMAND_NAME= "cs-sudo-command"

def create_temp_sudo_command_file():
    content = """#!/bin/bash
code="$@"
echo your_code: $code
echo ""
eval $code
"""
    global SUDO_COMMAND_NAME
    temp_sudo_command_filepath = f"/tmp/{SUDO_COMMAND_NAME}"
    LOG.info(f"create {temp_sudo_command_filepath} in host")
    with open(temp_sudo_command_filepath, 'w') as f:
        f.write(content)
    os.chmod(temp_sudo_command_filepath, 0o777)
    return temp_sudo_command_filepath
    


def create_tmp_sudoers_file(container_name):
    content = """#!/bin/bash
code="$1"
echo your code: $code
echo result:
eval $code"""

    temp_sudoers_filepath = f"/tmp/{container_name}-sudoers"
    with open(temp_sudoers_filepath, 'w') as f:
        f.write(content)
    os.chmod(temp_sudoers_filepath, 0o440)
    return temp_sudoers_filepath


def deal_with(container_name, user_group):
    global SUDO_COMMAND_NAME
    dest_sudo_command_path = f"/usr/bin/{SUDO_COMMAND_NAME}"

    LOG.info('check if you are in root')
    if not linux.check_is_root():
        raise Exception('need root permission')
    
    LOG.info(f'check if have container_name={container_name}')
    cmd = f"docker ps | grep {container_name}"
    success, result = common.execute_command(cmd)
    if not success:
        raise Exception(f'container named {container_name}')

    LOG.info(f'check container_name={container_name} have sudo command')
    cmd = f"docker exec {container_name} which sudo"
    success, result = common.execute_command(cmd)
    if not success:
        raise Exception(f'container named {container_name} not have sudo command')


    dest_sudoers = '/etc/sudoers'
    LOG.info(f'check container_name={container_name} if have {dest_sudoers}')
    cmd = f"docker exec {container_name} test -e {dest_sudoers}"
    success, result = common.execute_command(cmd)
    if not success:
        # LOG.info(f'no sudoers in container: {container_name}, create it')
        # create_tmp_sudoers_file(container_name)
        raise Exception(f'container named {container_name} not have {dest_sudoers} file')


    tmp_container_sudoers_filepath = f"/tmp/{container_name}-sudoers"
    LOG.info(f'cp container_name={container_name}:{dest_sudoers} to host {tmp_container_sudoers_filepath}')
    cmd = f"docker cp {container_name}:{dest_sudoers} {tmp_container_sudoers_filepath}"
    success, result = common.execute_command(cmd)
    if not success:
        raise Exception(f'docker cp {container_name}:{dest_sudoers} failed')

    


    
    temp_sudo_command_path = create_temp_sudo_command_file()

    
    LOG.info("modify host tmp_container_sudoers_filepath")
    os.chmod(tmp_container_sudoers_filepath, 0o777)
    with open(tmp_container_sudoers_filepath, 'r') as f:
        lines = f.readlines()

    add_str = f"{os.linesep}%{user_group} ALL=(root) NOPASSWD: {dest_sudo_command_path}{os.linesep}"
    for i, line in enumerate(lines):
        if "cs-sudo-command" in line:
            lines[i] = add_str
            break
    else:
        if i:
            lines.append(add_str)
    with open(f"/tmp/{container_name}-sudoers", 'w') as f:
        f.writelines(lines)
    os.chmod(f"/tmp/{container_name}-sudoers", 0o440)






    LOG.info(f"cp host {temp_sudo_command_path} to container={container_name}")
    cmd = f"docker cp {temp_sudo_command_path} {container_name}:{dest_sudo_command_path}"
    success, result = common.execute_command(cmd)
    if not success:
        raise Exception(f'docker cp file={temp_sudo_command_path} to {container_name} failed')


    LOG.info(f"cp host {tmp_container_sudoers_filepath} to container={container_name}")   
    cmd = f"docker cp {tmp_container_sudoers_filepath} {container_name}:{dest_sudoers}"
    success, result = common.execute_command(cmd)
    if not success:
        raise Exception(f'docker cp host {tmp_container_sudoers_filepath} to {container_name}:{dest_sudoers} failed')

    LOG.info(f'config {container_name} add {SUDO_COMMAND_NAME} success')
    LOG.info(f"use 'docker exec -it {container_name} bash' to test")


def main():
    parser = argparse.ArgumentParser(
        description=f'add sudo_command to /etc/sudoers',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("container_name", type=str, help="the container name to deal with")
    parser.add_argument("user_group", type=str, help="the user grout set in sudoers")
    args = parser.parse_args()
    
    deal_with(container_name=args.container_name, user_group=args.user_group)


if __name__ == '__main__':
    main()
