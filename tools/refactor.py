import json
import traceback
import argparse
from copy import deepcopy


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

    def get_args(self,):
        return self.parser.parse_args()


def process_line(out_file, single_json, mapper):
    json_response = json.loads(single_json)
    data = deepcopy(json_response['_source'])
    for key, value in data.items():
        new_key = mapper.get(key, key)
        json_response['_source'].pop(key)
        json_response['_source'][new_key] = value
    out_file.write(json.dumps(json_response, ensure_ascii=False) + '\n')


def main():
    args = Parser().get_args()
    input_file = args.input
    output_file = args.output
    mapper_file = args.mapper
    with open(mapper_file, 'r') as fp:
        mapper = json.load(fp)
    with open(output_file, 'w') as out_file:
        with open(input_file, 'r') as fp:
            for line_number, single_json in enumerate(fp, 1):
                try:
                    process_line(out_file, single_json, mapper)
                    print('Writing line number:', line_number)
                except Exception:
                    print('Error in line number:', line_number)
                    traceback.print_exc()
                    break


if __name__ == '__main__':
    main()
