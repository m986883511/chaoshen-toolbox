import argparse
import os
import logging

from chaoshen_toolbox.utils import linux
from chaoshen_toolbox.utils import common

LOG = logging.getLogger(__name__)


def create_temp_sudo_command_file():
    content = """#!/bin/bash
code="$1"
echo your code: $code
echo result:
eval $code"""

    with open("/tmp/sudo_command", 'w') as f:
        f.write(content)
    os.chmod("/tmp/sudo_command", 0o777)


def create_tmp_sudoers_file(container_name):
    content = """#!/bin/bash
code="$1"
echo your code: $code
echo result:
eval $code"""

    with open(f"/tmp/{container_name}-sudoers", 'w') as f:
        f.write(content)
    os.chmod(f"/tmp/{container_name}-sudoers", 0o440)


def deal_with(container_name, user_group):
    if not linux.check_is_root():
        raise Exception('need root permission')

    cmd = f"docker ps | grep {container_name}"
    success, result = common.execute_command(cmd)
    if not success:
        raise Exception(f'container named {container_name}')

    cmd = f"docker exec {container_name} which sudo"
    success, result = common.execute_command(cmd)
    if not success:
        raise Exception(f'container named {container_name} not have sudo command')

    cmd = f"docker exec {container_name} test -e /etc/sudoers"
    success, result = common.execute_command(cmd)
    if not success:
        # LOG.info(f'no sudoers in container: {container_name}, create it')
        # create_tmp_sudoers_file(container_name)
        raise Exception(f'container named {container_name} not have /etc/sudoers file')

    cmd = f"docker cp {container_name}:/etc/sudoers /tmp/{container_name}-sudoers"
    success, result = common.execute_command(cmd)
    if not success:
        raise Exception(f'docker cp {container_name}:/etc/sudoers failed')

    os.chmod(f"/tmp/{container_name}-sudoers", 0o777)
    with open(f"/tmp/{container_name}-sudoers", 'r') as f:
        lines = f.readlines()

    add_str = f"%{user_group} ALL=(root) NOPASSWD: /sudo_command"
    for i, line in enumerate(lines):
        if "sudo_command" in line:
            lines[i] = add_str
            break
    else:
        lines.append(add_str)

    with open(f"/tmp/{container_name}-sudoers", 'w') as f:
        f.writelines(lines)

    os.chmod(f"/tmp/{container_name}-sudoers", 0o440)
    cmd = f"docker cp /tmp/{container_name}-sudoers {container_name}:/etc/sudoers"
    success, result = common.execute_command(cmd)
    if not success:
        raise Exception(f'docker cp /tmp/{container_name}-sudoers to {container_name}:/etc/sudoers failed')

    cmd = f"docker cp /tmp/sudo_command {container_name}:/use/bin/sudo_command"
    success, result = common.execute_command(cmd)
    if not success:
        raise Exception(f'docker cp /tmp/sudo_command to {container_name}:/use/bin/sudo_command failed')

    LOG.info('config success')


def main():
    parser = argparse.ArgumentParser(
        description=f'add sudo_command to /etc/sudoers',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("container_name", type=str, help="the container name to deal with")
    parser.add_argument("user_group", type=str, help="the user grout set in sudoers")
    args = parser.parse_args()
    deal_with(container_name=args.container, user_group=args.user_group)


if __name__ == '__main__':
    main()
