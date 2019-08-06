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

PIPL_FIELDS = [
    'firstname',
    'lastname',
    'street',
    'city',
    'zip',
    'dateOfBirth',
    'court',
    'professionalLicense',
    'emails',
    'phone',
    'socialUrls'
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


def process_pipl(out_file, single_json, fields):
    single_json = re.sub(r'ObjectId\((.*?)\)', '\\1', single_json)
    single_json = re.sub(r'NumberInt\((.*?)\)', '\\1', single_json)
    json_response = json.loads(single_json)
    filtered_json = dict()
    for key, value in json_response.items():
        if key not in fields:
            continue
        if not value:
            continue
        if key == 'emails':
            for index, email in enumerate(value, 1):
                filtered_json.update({'email{}'.format(index): email})
        elif key == 'court' and value.get('civilCourtRecordCount'):
            filtered_json.update({
                'civilCourtRecordCount': value['civilCourtRecordCount']
            })
        elif key == 'socialUrls':
            fb_url = None
            for social in value:
                if social['domain'] == 'facebook.com' and\
                   '/people/' not in social['url']:
                    filtered_json.update({'facebookURL': social['url']})

                elif social['domain'] == 'linkedin.com':
                    filtered_json.update({'linkedinURL': social['url']})

                elif social['domain'] == 'twitter.com':
                    filtered_json.update({'twitterURL': social['url']})

                elif social['domain'] == 'amazon.com':
                    filtered_json.update({'amazonURL': social['url']})

                elif social['domain'] == '10Digits.us':
                    filtered_json.update({'10digitsURL': social['url']})

        else:
            filtered_json.update({key: value})
    out_file.write(json.dumps(filtered_json)+'\n')


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
                        process_pipl(out_file, single_json, FIELD_MAPS['pipl'])
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
