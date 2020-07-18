import json
import traceback
import argparse
from copy import deepcopy

EMAILS = ['e', 'e1', 'e2', 'e3', 'e4', 'e5']
IPS = ['ip', 'ip1', 'ip2', 'ip3', 'ip4', 'ip5']

KEYS_TO_CHECK = ['r']


KEY_LENGTH = 5
KEYS_WITH_LESS_CHARS = set()


class Parser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Refactoring JSON Keys')
        self.parser.add_argument(
            '-m', '--mapper', help='Input mapper json', required=True)
        self.parser.add_argument(
            '-i', '--input', help='Input File', required=True)
        self.parser.add_argument(
            '-o', '--output', help='Output File', required=True)
        self.parser.add_argument(
            '-chk', '--check', help='Checkfor few parameters', action='store_true')

    def get_args(self,):
        return self.parser.parse_args()


def process_line(out_file, single_json, mapper):
    global KEYS_WITH_LESS_CHARS
    json_response = json.loads(single_json)
    data = deepcopy(json_response['_source'])
    email = list()
    ip = list()
    error = not all(k in data.keys() for k in KEYS_TO_CHECK)
    for key, value in data.items():
        if len(key) < KEY_LENGTH:
            KEYS_WITH_LESS_CHARS.add(key)

        json_response['_source'].pop(key)
        if key in EMAILS:
            email.append(value)
        elif key in IPS:
            ip.append(value)
        else:
            new_key = mapper.get(key, key)
            json_response['_source'][new_key] = value
    if email:
        json_response['_source']['email'] = email[0]\
            if len(email) == 1 else email
    if ip:
        json_response['_source']['ip'] = ip[0] if len(ip) == 1 else ip
    out_file.write(json.dumps(json_response, ensure_ascii=False) + '\n')
    return error


def main():
    args = Parser().get_args()
    input_file = args.input
    output_file = args.output
    error_file = output_file.rsplit('/', 1)[0] + '/error.txt'\
        if '/' in output_file else 'error.txt'
    mapper_file = args.mapper
    with open(mapper_file, 'r') as fp:
        mapper = json.load(fp)
    err_file = open(error_file, 'w') if args.check else None
    with open(output_file, 'w') as out_file:
        with open(input_file, 'r') as fp:
            for line_number, single_json in enumerate(fp, 1):
                try:
                    error = process_line(out_file, single_json, mapper)
                    print('Writing line number:', line_number)
                    if error and err_file:
                        err_file.write(str(line_number) + '\n')
                except Exception:
                    print('Error in line number:', line_number)
                    traceback.print_exc()
                    break
    if err_file:
        err_file.write(
            f'Keys with length less than {KEY_LENGTH} '
            f'chars: {KEYS_WITH_LESS_CHARS}')


if __name__ == '__main__':
    main()
