import re
import traceback
import argparse
import csv


class Parser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Parsing Filter JSON Parameters')
        self.parser.add_argument(
            '-i', '--input', help='Input File', required=True)
        self.parser.add_argument(
            '-o', '--output', help='Output File', required=True)
        self.parser.add_argument(
            '-k', '--keep',
            help='list of fields/values to keep (comma separated). '
                 'Everything else will be ignored.',
            required=True)

    def get_args(self,):
        return self.parser.parse_args()


def process_line(line, fields, default_fields):
    data = dict()
    default_values = line.split(',')[:20]
    for k, v in zip(default_fields, default_values):
        data.update({k: v.strip('"')})
    for f in fields:
        if f not in line:
            continue
        match = re.findall(rf'{f}\":\s+\"?([^\"^,]+)', line)
        if not match:
            continue
        if 'null' in match[0]:
            continue
        if data.get(f):
            continue
        data.update({f: match[0].strip('"').strip('}')})
    print(data)
    return data


def main():
    args = Parser().get_args()
    input_file = args.input
    output_file = args.output
    fieldnames = args.keep.split(',')
    default_fields = [f'Field{i}' for i in range(1, 21)]
    default_fields.extend(fieldnames)
    with open(output_file, mode='w') as csv_file:
        writer = csv.DictWriter(
            csv_file, fieldnames=default_fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        with open(input_file, 'r') as fp:
            for line_number, line in enumerate(fp, 1):
                try:
                    print('Writing line number:', line_number)
                    data = process_line(line, fieldnames, default_fields)
                    if data:
                        writer.writerow(data)

                except Exception:
                    print('Error in line number:', line_number)
                    traceback.print_exc()
                    break


if __name__ == '__main__':
    main()
