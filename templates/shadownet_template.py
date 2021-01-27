# -- coding: utf-8 --
import os
import traceback
import utils
import dateutil.parser as dparser
import json

from .base_template import BaseTemplate


class ShadownetParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        self.folder_path = kwargs.get('folder_path')
        self.output_folder = kwargs.get('output_folder')
        self.parser_name = kwargs.get('sitename')
        
        self.main()

    def main(self):
        for _dir in os.listdir(self.folder_path):
            try:
                path = os.path.join(self.folder_path, _dir)
                if not os.path.isdir(path):
                    continue
                try:
                    _dir = _dir.lstrip("log_")
                    ts = dparser.parse(_dir).timestamp()
                except ValueError:
                    continue

                print(f'Proceeding for Folder {_dir}')
                with os.scandir(path) as dp:
                    for i in dp:
                        if not i.name.endswith('.log'):
                            continue

                        input_file_path = os.path.join(path, i.name)
                        if 'sender_' in i.name:
                            output_file_path = os.path.join(
                                self.output_folder, f'sender_{_dir}.json'
                            )
                            self.process_sender_file(
                                input_file_path, output_file_path, ts
                            )

                        if 'session_' in i.name:
                            output_file_path = os.path.join(
                                self.output_folder, f'session_{_dir}.json'
                            )
                            self.process_session_file(
                                input_file_path, output_file_path, ts
                            )

                print('----------------------------------------\n')
            except Exception:
                traceback.print_exc()
                continue

    def process_sender_file(self, input_file_path, output_file_path, ts):
        with open(input_file_path, 'r') as fp:
            content = fp.read()
            item = json.loads(content)

            data = {
                '_source': {
                    'type': 'message',
                    'site': self.parser_name,
                    'message': item['message'],
                    'sender': item['sender'],
                    'recipient': item['recipient'],
                    'ip': item['ip'],
                    'date': dparser.parse(item['timestamp']).timestamp()
                }
            }

            with open(output_file_path, 'a', encoding='utf-8') as file_pointer:
                utils.write_json(file_pointer, data)
        
            print(f'Json for  {input_file_path} written in {output_file_path}')
    
    def process_session_file(self, input_file_path, output_file_path, ts):
        with open(input_file_path, 'r') as fp:
            content = fp.read()
            item = json.loads(content)

            data = {
                '_source': {
                    'type': 'session',
                    'site': self.parser_name,
                    'site': item['user'],
                    'ip': item['ip'],
                    'date': dparser.parse(item['timestamp']).timestamp()
                }
            }

            with open(output_file_path, 'a', encoding='utf-8') as file_pointer:
                utils.write_json(file_pointer, data)
        
            print(f'Json for  {input_file_path} written in {output_file_path}')
