import csv
import os
import hmac
import base64
import json
import traceback
import argparse
import collections.abc
from glob import glob


ENC_KEY = "7C++Zx+hUufpL3YnrYj/vWNfDpMLgSJem+jsNDn1IgQ="


class Parser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Parsing Filter JSON Parameters')
        self.parser.add_argument(
            '-i', '--input_file', help='Input File')
        self.parser.add_argument(
            '-o', '--output_file', help='Output File')
        self.parser.add_argument(
            '-if', '--input_folder', help='Input Folder')
        self.parser.add_argument(
            '-of', '--output_folder', help='Output Folder')
        self.parser.add_argument(
            '-t', '--type', help='Input file type (csv/json)', required=True)

    def get_args(self,):
        return self.parser.parse_args()


def generate_hash(value):
    normalized_value = str(value).lower().strip().encode('utf-8')
    digested_value = hmac.digest(
        base64.b64decode(ENC_KEY),
        normalized_value,
        'sha256'
    )
    hashed_value = base64.standard_b64encode(digested_value).decode('utf-8')
    return hashed_value


def update_json(u, d=dict()):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_json(v, d.get(k, {}))
        elif isinstance(v, list):
            d[k] = [generate_hash(i) for i in v]
        else:
            d[k] = generate_hash(v)
    return d


def process_line(out_file, single_json):
    json_response = json.loads(single_json)
    hashed_json = update_json(json_response)
    out_file.write(json.dumps(hashed_json) + '\n')


def process_row(out_file, row):
    print(row)
    hashed_row = [generate_hash(r) for r in row]
    hashed_row_str = ','.join(hashed_row)
    out_file.write(hashed_row_str + '\n')


def main():
    args = Parser().get_args()
    input_folder = args.input_folder
    output_folder = args.output_folder
    input_file = args.input_file
    output_file = args.output_file
    file_type = args.type
    if not input_folder and not input_file:
        print('Input file/folder missing')
        return
    if input_folder and not output_folder:
        print('Output folder must be present when input folder is given')
        return
    if not output_file and not output_folder:
        print('Output file/folder missing')
        return
    if output_folder and not os.path.exists(output_folder):
        os.makedirs(output_folder)
    if file_type == 'json':
        if input_folder:
            for input_file in glob(f'{input_folder}/*.json'):
                output_file = os.path.join(
                    output_folder, input_file.rsplit('/')[-1])
                print(f"\nProcessing file {input_file.rsplit('/')[-1]}")
                with open(output_file, 'w') as out_file:
                    with open(input_file, 'r') as fp:
                        for line_number, single_json in enumerate(fp, 1):
                            try:
                                process_line(out_file, single_json)
                                print('Writing line number:', line_number)
                            except Exception:
                                print(f'Error in line number: '
                                      f'{line_number}, IGNORING')
        else:
            if output_folder:
                output_file = os.path.join(
                    output_folder, input_file.rsplit('/')[-1])
            print(f"\nProcessing file {input_file.rsplit('/')[-1]}")
            with open(output_file, 'w') as out_file:
                with open(input_file, 'r') as fp:
                    for line_number, single_json in enumerate(fp, 1):
                        try:
                            process_line(out_file, single_json)
                            print('Writing line number:', line_number)
                        except Exception:
                            print(f'Error in line number: '
                                  f'{line_number}, IGNORING')

    elif file_type == 'csv':
        if input_folder:
            for input_file in glob(f'{input_folder}/*.csv'):
                output_file = os.path.join(
                    output_folder, input_file.rsplit('/')[-1])
                print(f"\nProcessing file {input_file.rsplit('/')[-1]}")
                with open(output_file, 'w') as out_file:
                    with open(input_file, 'r') as fp:
                        reader = csv.reader(fp)
                        for line_number, row in enumerate(reader, 1):
                            try:
                                process_row(out_file, row)
                                print('Writing line number:', line_number)
                            except Exception:
                                print(f'Error in line number: '
                                      f'{line_number}, IGNORING')
        else:
            if output_folder:
                output_file = os.path.join(
                    output_folder, input_file.rsplit('/')[-1])
            print(f"\nProcessing file {input_file.rsplit('/')[-1]}")
            with open(output_file, 'w') as out_file:
                with open(input_file, 'r') as fp:
                    reader = csv.reader(fp)
                    for line_number, row in enumerate(reader, 1):
                        try:
                            process_row(out_file, row)
                            print('Writing line number:', line_number)
                        except Exception:
                            print(f'Error in line number: '
                                  f'{line_number}, IGNORING')
    else:
        print('Invalid file type')


if __name__ == '__main__':
    main()
