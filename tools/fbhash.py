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
            '-i', '--input', help='Input File', required=True)
        self.parser.add_argument(
            '-o', '--output', help='Output File', required=True)

    def get_args(self,):
        return self.parser.parse_args()


def generate_hash(value):
    normalized_value = str(value).lower().strip().encode('utf-8')
    digested_value = hmac.digest(
        ENC_KEY.encode('utf-8'),
        normalized_value,
        'sha256'
    )
    hashed_value = base64.standard_b64encode(digested_value).decode('utf-8')
    return hashed_value


def update_json(u, d=dict()):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_json(v, d.get(k, {}))
        else:
            d[k] = generate_hash(v)
    return d


def process_line(out_file, single_json):
    json_response = json.loads(single_json)
    hashed_json = update_json(json_response)
    out_file.write(json.dumps(hashed_json) + '\n')


def main():
    args = Parser().get_args()
    input_folder = args.input
    output_folder = args.output
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for input_file in glob(f'{input_folder}/*.json'):
        output_file = os.path.join(output_folder, input_file.rsplit('/')[-1])
        print(f"\nProcessing file {input_file.rsplit('/')[-1]}")
        with open(output_file, 'w') as out_file:
            with open(input_file, 'r') as fp:
                for line_number, single_json in enumerate(fp, 1):
                    try:
                        process_line(out_file, single_json)
                        print('Writing line number:', line_number)
                    except Exception:
                        print(f'Error in line number: {line_number}, IGNORING')


if __name__ == '__main__':
    main()
