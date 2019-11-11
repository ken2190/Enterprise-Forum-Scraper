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
        self.parser.add_argument(
            '-k', '--keep', help='list of fields/values to keep (comma separated). Everything else will be removed.', required=True)
        self.parser.add_argument(
            '-d', '--domain', help='add domain field from email', action='store_true')
        self.parser.add_argument(
            '-am', '--address_merge', help='merge addresses', action='store_true')
        self.parser.add_argument(
            '-nm', '--name_merge', help='merge names', action='store_true')
        self.parser.add_argument(
            '-f', '--format', help='Insert formatting for elasticsearch', action='store_true')

    def get_args(self,):
        return self.parser.parse_args()


def process_line(out_file, single_json, args):
    out_fields = args.keep
    out_fields = [i.strip() for i in out_fields.split(',')] if out_fields else []
    json_response = json.loads(single_json)
    address = 'city state zip'
    name = 'fn ln'
    final_data = dict()
    if '_source' in json_response:
        data = json_response['_source'].items()
    else:
        data = json_response.items()
    for key, value in data:
        if out_fields and key not in out_fields:
            continue
        if key in ['email', 'e'] and args.domain:
            domain = value.split('@')[-1]
            final_data.update({'domain': domain})
        if key in ['city', 'state', 'zip'] and args.address_merge:
            address = address.replace(key, value)
            final_data.update({'address': address})  
            continue
        if key in ['fn', 'ln'] and args.name_merge:
            name = name.replace(key, value)
            final_data.update({'n': name})  
            continue

        final_data.update({key: value})
    if args.format:
        filtered_json = {'_source': final_data}
    else:
        filtered_json = final_data
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
                except:
                    print('Error in line number:', line_number)
                    traceback.print_exc()
                    break


if __name__ == '__main__':
    main()

