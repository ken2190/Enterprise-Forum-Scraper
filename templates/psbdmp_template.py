# -- coding: utf-8 --
import os
import re
from collections import OrderedDict
import traceback
import json
import utils
import datetime
import dateutil.parser as dparser
from lxml.html import fromstring


class BrokenPage(Exception):
    pass


class PsbdmpParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.output_folder = output_folder
        self.folder_path = folder_path
        self.error_folder = "{}/Errors".format(output_folder)
        # main function
        self.main()

    def main(self):
        for _dir in os.listdir(self.folder_path):
            try:
                path = os.path.join(self.folder_path, _dir)
                if not os.path.isdir(path):
                    continue
                try:
                    ts = dparser.parse(_dir).timestamp()
                except ValueError:
                    continue
                print(f'Proceeding for Folder {_dir}')
                with os.scandir(path) as dp:
                    for i in dp:
                        if not i.name.endswith('.txt'):
                            continue
                        input_file_path = os.path.join(path, i.name)
                        output_file_path = os.path.join(
                            self.output_folder, f'{_dir}.json')
                        self.process_file(
                            input_file_path, output_file_path, ts)
                print('----------------------------------------\n')
            except Exception:
                traceback.print_exc()
                continue

    def process_file(self, input_file_path, output_file_path, ts):
        paste_id = input_file_path.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        data = {
            'source': 'pastebin',
            'date': ts,
            'paste_id': paste_id

        }
        with open(input_file_path, 'r') as fp:
            content = fp.read()
            data.update({'content': content})
            with open(output_file_path, 'a', encoding='utf-8') as file_pointer:
                utils.write_json(file_pointer, data)
                print(f'Json for paste_id {paste_id} '
                      f'written in {output_file_path}')
