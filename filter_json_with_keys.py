import sys
import re
import csv
import json
import traceback
import argparse

PIZAP_FIELDS = [
    'UserName',
    'Name',
    'Email',
    'FBUserID',
    'ProfileImage',
    'Password',
    'CountryCode'
]
GYFCAT_FIELDS = [
    'username',
    'email',
    'password',
]

FIELD_MAPS = {
    'pizap': PIZAP_FIELDS,
    'gyfcat': GYFCAT_FIELDS
}


class Parser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Parsing Filter JSON Parameters')
        self.parser.add_argument(
            '-i', '--input', help='Input File', required=True)
        self.parser.add_argument(
            '-o', '--output', help='Output File', required=True)
        self.parser.add_argument(
            '-t', '--type', help='JSON Type', required=True)

    def get_args(self,):
        return self.parser.parse_args()


def process_line(out_file, single_json, _type):
    fields = FIELD_MAPS[_type]
    match = re.findall(r'.*?({.*})', single_json)
    if not match:
        print('Following line is not valid JSON')
        print(single_json)
        return
    try:
        json_response = json.loads(match[0])
    except:
        print('Following line is not valid JSON')
        print(single_json)
        return
    filtered_json = dict()
    for key, value in json_response.items():
        if key in fields:
            filtered_json.update({key: list(value.values())[0]})
    out_file.write(json.dumps(filtered_json)+'\n')


def process_file(args):
    input_file = args.input
    output_file = args.output
    with open(output_file, 'w') as out_file:
        with open(input_file, 'r') as fp:
            for line_number, single_json in enumerate(fp, 1):
                try:
                    process_line(out_file, single_json, args.type)
                except:
                    print('Error in line number:', line_number)
                    traceback.print_exc()
                    break


def main():
    args = Parser().get_args()
    if args.type not in FIELD_MAPS:
        print('Invalid JSON type')
        return
    process_file(args)


if __name__ == '__main__':
    main()
