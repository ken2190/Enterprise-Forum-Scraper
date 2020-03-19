import json
import traceback
import argparse


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


def process_line(out_file, single_json, args):
    json_response = json.loads(single_json)
    final_data = dict()
    if '_source' in json_response:
        data = json_response['_source'].items()
    else:
        data = json_response.items()
    for key, value in data:
        if not value:
            continue
        if key in ['@version', '@timestamp']:
            continue

        final_data.update({key: value})
    filtered_json = {'_source': final_data}
    out_file.write(json.dumps(filtered_json)+'\n')


def main():
    args = Parser().get_args()
    input_file = args.input
    output_file = args.output
    with open(output_file, 'w') as out_file:
        with open(input_file, 'r') as fp:
            for line_number, single_json in enumerate(fp, 1):
                try:
                    process_line(out_file, single_json, args)
                    print('Writing line number:', line_number)
                except Exception:
                    print('Error in line number:', line_number)
                    traceback.print_exc()
                    break


if __name__ == '__main__':
    main()

