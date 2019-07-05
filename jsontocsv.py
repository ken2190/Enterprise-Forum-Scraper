import sys
import re
import csv
import json
import traceback
COLUMNS = [
    'first_name',
    'last_name',
    'email',
    'address',
    'address2',
    'city',
    'state',
    'country',
    'zip',
    'ip_address',
    'phone',
    'carrier'
]


def write_json_to_file(csv_writer, single_json):
    data = re.sub(r'\s{2,}', '', single_json)
    data = data.split(',')
    data = [
        i.replace('}', '').replace('{', '').strip()
        for i in data
    ]
    data = [
        i for i in data
        if any(col == i.split(':')[0].replace('"', '')
               for col in COLUMNS)
    ]
    mydict = dict()
    for field in data:
        key = field.split(':')[0].replace('"', '')
        value = ':'.join(field.split(':')[1:]).replace('"', "'")
        value = re.sub(r'NumberLong\((.*?)\)', '\\1', value)
        try:
            if key not in ['phone', 'ip_address'] and int(value):
                value = ''
            if key == 'zip' and len(value) > 5 and int(value):
                value = ''
        except:
            pass
        mydict.update({
            key.strip(): value.strip()
        })
    csv_writer.writerow(mydict)


def process_for_indentation(input_file, output_file):
    with open(output_file, 'w') as csvfile:
        csv_writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)
        csv_writer.writeheader()
        with open(input_file, 'r') as fp:
            single_json = ''
            for line_number, line in enumerate(fp, 1):
                try:
                    if '}' not in line.rstrip('\n'):
                        single_json += line.strip('\n')
                        continue
                    write_json_to_file(csv_writer, single_json)
                    single_json = ''
                except:
                    print('Error in line number:', line_number)
                    traceback.print_exc()
                    break


def process_without_indentation(input_file, output_file):
    with open(output_file, 'w') as csvfile:
        csv_writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)
        csv_writer.writeheader()
        with open(input_file, 'r') as fp:
            for line_number, single_json in enumerate(fp, 1):
                try:
                    write_json_to_file(csv_writer, single_json)
                except:
                    print('Error in line number:', line_number)
                    traceback.print_exc()
                    break

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(
            'Invalid arguments;\n'
            'Usage: "python jsontocsv.py <input_file> <output_file> <indentation>(optional)"\n'
            'indentaion: false(default) or true'
        )
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    indentation = sys.argv[3] if len(sys.argv) == 4 else 'false'
    if indentation.lower() == 'true':
        process_for_indentation(input_file, output_file)
    else:
        process_without_indentation(input_file, output_file)
