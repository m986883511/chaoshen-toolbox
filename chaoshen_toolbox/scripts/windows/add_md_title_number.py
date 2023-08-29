import argparse

from chaoshen_toolbox import LOG
from chaoshen_toolbox.utils import file


def work(file_path):
    contents = file.read_file_list(file_path)
    record = list(range(10))

    for n, line in enumerate(contents):
        if line.startswith(b'# '):
            record[0] += 1
            record[1] = 0
            contents[n] = line[:2] + '{}、 '.format(record[0]).encode() + line[2:]
        elif line.startswith(b'## '):
            record[1] += 1
            record[2] = 0
            contents[n] = line[:3] + '{}.{} '.format(record[0], record[1]).encode() + line[3:]
        elif line.startswith(b'### '):
            record[2] += 1
            record[3] = 0
            contents[n] = line[:4] + '{}.{}.{} '.format(record[0], record[1], record[2]).encode() + line[4:]
        elif line.startswith(b'#### '):
            record[3] += 1
            record[4] = 0
            contents[n] = line[:5] + '{}.{}.{}.{} '.format(record[0], record[1], record[2], record[3]).encode() + line[5:]
    new_name = file.add_suffix_to_file(file_path, 'new')
    file.write_file_list(contents, new_name)


def main():
    parser = argparse.ArgumentParser(description='add title number to md file')
    parser.add_argument('md_file', help='md file path')
    args = parser.parse_args()
    LOG.info(f"{__file__} execute with args={args.__dict__}")
    work(args.md_file)


if __name__ == '__main__':
    main()
