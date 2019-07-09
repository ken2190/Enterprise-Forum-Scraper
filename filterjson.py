import sys
import re
import csv
import json
import traceback

IP_PATTERN = re.compile(
    r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
)


def process_line(out_file, single_json):
    json_response = json.loads(single_json)
    filtered_json = dict()
    for key, value in json_response.items():
        if not value:
            continue
        if key == 'phone':
            filtered_json.update({key: value})
            continue
        if key == 'ip_address':
            if IP_PATTERN.search(value):
                filtered_json.update({key: value})
            continue
        try:
            if key == 'zip':
                if len(value) > 5 and int(value):
                    continue
                else:
                    filtered_json.update({key: value})
            if int(value):
                continue
        except:
            filtered_json.update({key: value})
    out_file.write(json.dumps(filtered_json)+'\n')


def filter_numbers(input_file, output_file):
    with open(output_file, 'w') as out_file:
        with open(input_file, 'r') as fp:
            for line_number, single_json in enumerate(fp, 1):
                try:
                    process_line(out_file, single_json)
                except:
                    print('Error in line number:', line_number)
                    traceback.print_exc()
                    break

if __name__ == '__main__':
    if not len(sys.argv) == 3:
        print(
            'Invalid arguments;\n'
            'Usage: "python jsontocsv.py <input_file> <output_file>'
        )
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    filter_numbers(input_file, output_file)
