import argparse
import re
import os

from chaoshen_toolbox import LOG


def check_file_have_crlf(file_path):
    with open(file_path, 'rb') as f:
        text = f.read()
    regex = re.compile(rb"[^\r\n]+", re.MULTILINE)
    content = regex.match(text)
    print(content)
    return bool(content)


def get_all_files(dir_path):
    for (dirpath, dirnames, filenames) in os.walk(dir_path):
        for f in filenames:
            yield os.path.join(dirpath, f)


def main():
    parser = argparse.ArgumentParser(description='find crlf files')
    parser.add_argument('-d', '--dir', default='./', help='default is current dir')
    parser.add_argument('-e', '--ext', default='py', help='default is for python files')
    args = parser.parse_args()
    LOG.info(f"{__file__} execute with args={args.__dict__}")
    for file_path in get_all_files(args.dir):
        if file_path.endswith(args.ext):
            if check_file_have_crlf(file_path):
                print(file_path)
                break


if __name__ == '__main__':
    main()
