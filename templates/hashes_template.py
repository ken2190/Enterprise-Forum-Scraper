# -- coding: utf-8 --
import os
import traceback
import utils
import dateutil.parser as dparser
import json

from .base_template import BaseTemplate


class HashesParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # main function
        self.main()

    def main(self):
        for file_name in os.listdir(self.folder_path):
            try:
                path = os.path.join(self.folder_path, file_name)
                if os.path.isdir(path):
                    continue

                print(f'Proceeding for File {file_name}')

                input_file_path = path
                output_file_name = file_name.rstrip('.txt')
                output_file_path = os.path.join(
                    self.output_folder, f'{output_file_name}.json'
                )

                self.process_file(
                    input_file_path, output_file_path
                )

                print('----------------------------------------\n')
            except Exception:
                traceback.print_exc()
                continue

    def process_file(self, input_file_path, output_file_path):
        with open(input_file_path, 'r') as fp:
            content = fp.read()

            for row in content.split("\n"):
                row = row.strip()
                
                if row:
                    hash_type = row.split(" ")[0]
                    hash_content = row.split(" ")[1]

                    if len(hash_content.split(":")) == 3:
                        hash_value = hash_content.split(":")[0]
                        hash_salt = hash_content.split(":")[1]
                        hash_plain = hash_content.split(":")[2]
                    else:
                        hash_value = hash_content.split(":")[0]
                        hash_salt = ''
                        hash_plain = hash_content.split(":")[1]
                    
                    data = {
                        '_source': {
                            'source': 'hashes.org',
                            "type": 'hash',
                            'hashtype': hash_type,
                            'hash': hash_value,
                            'salt': hash_salt,
                            'value': hash_plain
                        }
                    }

                    with open(output_file_path, 'a', encoding='utf-8') as file_pointer:
                        utils.write_json(file_pointer, data)
                    
            print(f'Json for paste_id {input_file_path} '
                f'written in {output_file_path}')
