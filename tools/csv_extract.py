import re
import traceback
import argparse
import csv


class Parser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='''
                 .d8888b.  .d8888b. 888     888                888                          888
                d88P  Y88bd88P  Y88b888     888                888                          888
                888    888Y88b.     888     888                888                          888
                888        "Y888b.  Y88b   d88P .d88b. 888  888888888888d888 8888b.  .d8888b888888
                888           "Y88b. Y88b d88P d8P  Y8b`Y8bd8P'888   888P"      "88bd88P"   888
                888    888      "888  Y88o88P  88888888  X88K  888   888    .d888888888     888
                Y88b  d88PY88b  d88P   Y888P   Y8b.    .d8""8b.Y88b. 888    888  888Y88b.   Y88b.
                 "Y8888P"  "Y8888P"     Y8P     "Y8888 888  888 "Y888888    "Y888888 "Y8888P "Y888
                 
	               Extract data from a CSV file into a new CSV file.
                       Specify which columns you want to keep using -k
                ''')
        self.parser.add_argument(
            '-i', '--input', help='Input File', required=True)
        self.parser.add_argument(
            '-o', '--output', help='Output File', required=True)
        self.parser.add_argument(
            '-k', '--keep',
            help='list of columns/values to keep (comma separated). '
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
