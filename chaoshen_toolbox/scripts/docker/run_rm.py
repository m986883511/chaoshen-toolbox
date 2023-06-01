#!/usr/bin/env python
# auther: wc
# filename: /usr/bin/docker-run-rm
import argparse

from chaoshen_toolbox.utils import common

docker_module = common.check_require_pip_package("docker", package_install_name="docker")
client = docker_module.from_env()
containers = client.containers.list()
container_names = [i.name for i in containers]


def get_attr(name):
    container = client.containers.get(name)
    return container.attrs


def run_rm_it(name):
    attr = get_attr(name)
    print(attr)
    image = attr['Config']['Image']
    env_list = ["-e {}='{}'".format(i.split('=')[0], i.split('=')[1]) for i in attr['Config']['Env']]
    env_str = ' '.join(env_list)
    mount = attr['Mounts']
    mount_list = ["-v {}:{}".format(_mount['Source'], _mount['Destination']) for _mount in mount]
    mount_str = ' '.join(mount_list)
    print(image)
    for i in env_list:
        print(i)
    for i in mount_list:
        print(i)
    docker_run_rm = 'docker run --rm -it --name debug_{} --net=host {} {} --privileged --entrypoint /bin/bash {} '.format(
        name, env_str, mount_str, image)
    print('')
    print('full command:')
    print(docker_run_rm)


def main():
    parser = argparse.ArgumentParser(description='get command for a container')
    parser.add_argument('container_name', type=str, help='one exist container name')
    args = parser.parse_args()
    run_rm_it(args.container_name)


if __name__ == '__main__':
    main()
