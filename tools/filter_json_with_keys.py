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

PIPL_FIELDS = {
    'firstname': 'fn',
    'lastname': 'ln',
    'middlename': 'mn',
    'street': 'a1',
    'city': 'a2',
    'zip': 'a3',
    'dateOfBirth': 'dob',
    'phone': 't',
}
TO_REMOVE_PIPL = [
    '_id',
    'id',
    'title',
    'age',
    'dateUpdated',
    'gender',
    'politicalParty',
    'race',
    'religion',
    'aka'
]

FIELD_MAPS = {
    'pizap': PIZAP_FIELDS,
    'gyfcat': GYFCAT_FIELDS,
    'pipl': PIPL_FIELDS
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


def process_pipl(out_file, single_json):
    single_json = re.sub(r'ObjectId\((.*?)\)', '\\1', single_json)
    single_json = re.sub(r'NumberInt\((.*?)\)', '\\1', single_json)
    json_response = json.loads(single_json)
    filtered_json = dict()
    for key, value in json_response.items():
        if key in TO_REMOVE_PIPL:
            continue
        if not value:
            continue
        if key == 'emails':
            for index, email in enumerate(value, 1):
                filtered_json.update({'e{}'.format(index): email})
        elif key == 'socialUrls':
            for social in value:
                if social['domain'] == 'facebook.com' and\
                   '/people/' not in social['url']:
                    filtered_json.update({'fb': social['url']})

                elif social['domain'] == 'linkedin.com':
                    filtered_json.update({'linkedin': social['url']})

                elif social['domain'] == 'twitter.com':
                    filtered_json.update({'twitter': social['url']})

                elif social['domain'] == 'amazon.com':
                    filtered_json.update({'amazon': social['url']})

                elif social['domain'].lower() == '10digits.us':
                    filtered_json.update({'10digits': social['url']})
                elif social['domain'].lower() == 'pinterest.com':
                    filtered_json.update({'pinterest': social['url']})

        elif key in PIPL_FIELDS:
            filtered_json.update({PIPL_FIELDS[key]: value})
        else:
            filtered_json.update({key: value})
    process_address(filtered_json)
    process_name(filtered_json)
    out_file.write(json.dumps(filtered_json)+'\n')


def process_address(filtered_json):
    address = ''
    if 'a1' in filtered_json:
        address = filtered_json.pop('a1')
    if 'a2' in filtered_json:
        address = f"{address} {filtered_json.pop('a2')}"
    if 'state' in filtered_json:
        address = f"{address} {filtered_json.pop('state')}"
    if 'a3' in filtered_json:
        address = f"{address} {filtered_json.pop('a3')}"
    if address:
        filtered_json.update({'a': address})


def process_name(filtered_json):
    name = ''
    if 'fn' in filtered_json:
        name = filtered_json.pop('fn')
    if 'mn' in filtered_json:
        name = f"{name} {filtered_json.pop('mn')}"
    if 'ln' in filtered_json:
        name = f"{name} {filtered_json.pop('ln')}"
    if name:
        filtered_json.update({'n': name})
    pass


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
                    if not args.type == 'pipl':
                        process_line(out_file, single_json, args.type)
                    else:
                        process_pipl(out_file, single_json)
                    print('Writing line number:', line_number)
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