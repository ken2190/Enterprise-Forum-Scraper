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
        self.parser_name = 'shadownet'
        self.sitename = kwargs.get('sitename')
        self.main()

    def main(self):
        for domain_dir in os.listdir(self.folder_path):
            try:
                domain_dir_path = os.path.join(self.folder_path, domain_dir)
                if not os.path.isdir(domain_dir_path):
                    continue
                
                print("="*100)
                print(f'Proceeding for log folder for  {domain_dir}\n')

                output_folder = os.path.join(self.output_folder, domain_dir)
                if not os.path.isdir(output_folder):
                    os.makedirs(output_folder)

                for log_dir in os.listdir(domain_dir_path):
                    log_dir_path = os.path.join(domain_dir_path, log_dir)
                    if not os.path.isdir(log_dir_path):
                        continue

                    try:
                        _dir = log_dir.lstrip("log_")
                        ts = dparser.parse(_dir).timestamp()
                    except ValueError:
                        continue

                    output_file_path = os.path.join(
                        output_folder, f'{_dir}.json'
                    )

                    file_pointer = open(output_file_path, 'w', encoding='utf-8')
                    with os.scandir(log_dir_path) as dp:
                        for i in dp:
                            if not i.name.endswith('.log'):
                                continue

                            input_file_path = os.path.join(log_dir_path, i.name)
                            if 'sender_' in i.name:
                                self.process_sender_file(
                                    input_file_path, file_pointer, ts, domain_dir
                                )

                            if 'session_' in i.name:
                                self.process_session_file(
                                    input_file_path, file_pointer, ts, domain_dir
                                )

                            if 'registration' in i.name:
                                self.process_registration_file(
                                    input_file_path, file_pointer, ts, domain_dir
                                )

                    print(f'Json written in {output_file_path}')
                    print('----------------------------------------\n')
            except Exception:
                traceback.print_exc()
                continue

    def process_sender_file(self, input_file_path, file_pointer, ts, domain_dir):
        with open(input_file_path, 'r') as fp:
            content = fp.read()

            for line in content.split("\n"):
                if line:
                    item = json.loads(line)

                    try:
                        sender = item['sender'].split("/")[0]
                    except:
                        sender = item['sender']
                    
                    try:
                        recipient = item['recipient'].split("/")[0]
                    except:
                        recipient = item['recipient']

                    data = {
                        '_source': {
                            'type': 'message',
                            'site': domain_dir,
                            'message': item['message'],
                            'sender': sender,
                            'recipient': recipient,
                            'ip': item['ip'],
                            'date': dparser.parse(item['timestamp']).timestamp()
                        }
                    }

                    if len(item['sender'].split("/")) > 1:
                        sender_resource = item['sender'].split("/")[1]
                        if sender_resource:
                            data["_source"]["sender_resource"] = sender_resource

                    if len(item['recipient'].split("/")) > 1:
                        recipient_resource = item['recipient'].split("/")[1]
                        if recipient_resource:
                            data["_source"]["recipient_resource"] = recipient_resource

                    utils.write_json(file_pointer, data)
        
    def process_session_file(self, input_file_path, file_pointer, ts, domain_dir):
        with open(input_file_path, 'r') as fp:
            content = fp.read()

            for line in content.split("\n"):
                if line:
                    item = json.loads(line)

                    try:
                        user = item['user'].split("/")[0]
                    except:
                        user = item['user']

                    data = {
                        '_source': {
                            'type': 'session',
                            'site': domain_dir,
                            'user': user,
                            'ip': item['ip'].replace("::ffff:", ''),
                            'date': dparser.parse(item['timestamp']).timestamp()
                        }
                    }

                    if len(item['user'].split("/")) > 1:
                        resource = item['user'].split("/")[1]
                        if resource:
                            data["_source"]["resource"] = resource

                    utils.write_json(file_pointer, data)
        
    def process_registration_file(self, input_file_path, file_pointer, ts, domain_dir):
        with open(input_file_path, 'r') as fp:
            content = fp.read()

            for line in content.split("\n"):
                if line:
                    item = json.loads(line)

                    try:
                        user = item['user'].split("/")[0]
                    except:
                        user = item['user']

                    data = {
                        '_source': {
                            'type': 'registration',
                            'site': domain_dir,
                            'server': item['server'],
                            'user': user,
                            'email': item['email'],
                            'password': item['password'],
                            'date': dparser.parse(item['timestamp']).timestamp()
                        }
                    }

                    if len(item['user'].split("/")) > 1:
                        resource = item['user'].split("/")[1]
                        if resource:
                            data["_source"]["resource"] = resource

                    utils.write_json(file_pointer, data)
