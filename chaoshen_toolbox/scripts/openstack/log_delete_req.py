import argparse
import os
import re

from chaoshen_toolbox.utils import file

usage = """
A example like follow, just delete [req-*]
\u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193
2023-05-30 16:12:40.658 19059 INFO nova.compute.manager [req-47ce1786-eb8e-4ac8-ac9a-aad38af1400a 90bd088c758b4b0787bf153626d9b91d 9783fe0f8b0549f98528967424c50f2f - default default] [instance: 3409a7cf-16a1-4003-8e07-0db6f08d24c5] Rebuilding instance
\u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193
2023-05-30 16:12:40.658 19059 INFO nova.compute.manager Rebuilding instance
"""


def deal_with(file_path):
    if not os.path.isfile(file_path):
        raise Exception(f'file {file_path} not exist')

    new_filepath = file.add_suffix_to_file(file_path, 'noreq')
    regex = r"\[req-.*?\]"
    with open(file_path, 'r') as f:
        lines = f.readlines()
    with open(new_filepath, 'w') as f:
        for line in lines:
            line = re.sub(regex, "", line)
            f.write(line)


def main():
    parser = argparse.ArgumentParser(
        description=f'delete file req and generate newfile\n{usage}',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("log_filepath", type=str, help="the log file need to deal with")
    args = parser.parse_args()
    deal_with(file_path=args.log_filepath)


if __name__ == '__main__':
    main()
