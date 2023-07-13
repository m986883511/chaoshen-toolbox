import argparse
import os
import re

from pydantic import BaseModel

from chaoshen_toolbox.utils import file, common
from chaoshen_toolbox import LOG

usage = """
A example like follow, just delete [req-*]
\u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193
2023-05-30 16:12:40.658 19059 INFO nova.compute.manager [req-47ce1786-eb8e-4ac8-ac9a-aad38af1400a 90bd088c758b4b0787bf153626d9b91d 9783fe0f8b0549f98528967424c50f2f - default default] [instance: 3409a7cf-16a1-4003-8e07-0db6f08d24c5] Rebuilding instance
\u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193  \u2193
2023-05-30 16:12:40.658 19059 INFO nova.compute.manager Rebuilding instance
"""


class ArgsModel(BaseModel):
    log_filepath: str
    connector: str = '--'
    no_block: str = ""
    no_req: bool = False
    no_level: bool = False


def get_new_filepath(args: ArgsModel):
    all_no_items = common.get_basemodel_class_variable_names(ArgsModel)
    new_filepath = args.log_filepath
    for no_item in all_no_items:
        if not no_item.startswith('no_'):
            continue
        if getattr(args, no_item):
            no_item = no_item.replace('_', '').replace('-', '')
            LOG.info(f'will add {no_item} to newfile')
            new_filepath = file.add_suffix_to_file(new_filepath, no_item, connector=args.connector)
    LOG.info(f"new_filepath is {new_filepath}")
    return new_filepath


def deal_with_args(args: ArgsModel):
    if not os.path.isfile(args.log_filepath):
        raise Exception(f'file {args.log_filepath} not exist')

    regex = r"\[.*?req-.*?\]"
    with open(args.log_filepath, 'r') as f:
        lines = f.readlines()

    new_filepath = get_new_filepath(args)
    if new_filepath == args.log_filepath:
        LOG.warning("new_filepath == args.log_filepath, should do nothing")
        return

    with open(new_filepath, 'w') as f:
        new_lines = []
        for line in lines:

            if args.no_req:
                line = re.sub(regex, "", line)
            if args.no_level:
                pass
            if args.no_block:
                line_list = line.split(' ')
                need_delete_blocks = [int(i) for i in args.no_block.split(',')]
                for block in need_delete_blocks:
                    line_list[block] = ''
                line = ' '.join(line_list).strip()
            line = re.sub(r'\s+', ' ', line)
            new_lines.append(line.rstrip()+os.linesep)
        f.writelines(new_lines)


def main():
    parser = argparse.ArgumentParser(
        description=f'delete file req and generate newfile\n{usage}',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("log_filepath", type=str, help="the log file need to deal with")
    parser.add_argument("-c", "--connector", default='--', help="the log file need to deal with")
    parser.add_argument("--no-req", action="store_true", help="the log file need to deal with")
    parser.add_argument("--no-level", action="store_true", help="the log file need to deal with")
    parser.add_argument("--no-block", default="", help="the log file need to deal with")

    args = parser.parse_args()
    args = ArgsModel(**vars(args))
    deal_with_args(args)


if __name__ == '__main__':
    main()
