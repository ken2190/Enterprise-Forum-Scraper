import re
import json
import os
import csv
from lxml.html import fromstring
from lxml.etree import ParserError
from glob import glob

PATH = '/Users/umeshpathak/Downloads/RF_LOGS'


def parse_file(f):
    value = re.findall(r'\((\d+_\d+)\)', f)[0]
    with open(f, 'r') as fp:
        raw_content = fp.read()
        try:
            html_response = fromstring(raw_content)
        except ParserError:
            return []
        rows = html_response.xpath(
            '//div[contains(@class, "msgShout msglog")]')
        rows.reverse()
        data = list()
        for row in rows:
            user = row.xpath(
                'span[@class="username_msgShout"]/'
                'span[@class="god-hex" or @class="vip-hex" '
                'or @class="member-hex" or @class="leet-hex"'
                'or @class="mvp-hex" or @class="adv-hex"'
                'or @class="tryhard-hex" or @class="mvp-modp-hex"'
                'or @class="elite-hex" or @class="owner-hex"'
                'or @class="uber-hex"'
                ']/descendant::text()')

            if not user:
                user = row.xpath(
                    'span[@class="username_msgShout"]/'
                    'span[@style]/text()')

            if not user:
                user = row.xpath(
                    'span[@class="username_msgShout"]/'
                    'span[@id]/following-sibling::span[1]/'
                    'descendant::text()')

            if not user:
                user = row.xpath(
                    'span[@class="username_msgShout"]/'
                    'span/descendant::text()')

            if not user:
                user = row.xpath(
                    'span[@class="username_msgShout"]//'
                    'img/@original-title')

            message = ' '.join(row.xpath(
                'span[@class="content_msgShout"]/descendant::text()'))
            if message.startswith('posted new thread'):
                continue
            # data.append({'user': ' '.join(user), 'message': message, 'f_name': value})
            data.append({
                '_source': {
                    'user': ' '.join(user),
                    'message': message
                }
            })
        return data


def write_json(file_pointer, data):
    """
    writes `data` in file object `file_pointer`.
    """
    json_file = json.dumps(data, indent=4, ensure_ascii=False)
    file_pointer.write(json_file)
    file_pointer.write('\n')


def get_files():
    files = []
    for filee in glob(PATH+'/*'):
        if os.path.isfile(filee):
            files.append(filee)

    pattern = re.compile(r'log\((\d+)_\d+\)')

    sorted_files = sorted(
        files,
        key=lambda x: int(pattern.search(x).group(1)))

    filtered_files = list()
    seen = set()
    for x in sorted_files:
        value = re.findall(r'\((\d+_\d+)\)', x)[0]
        if value not in seen:
            seen.add(value)
            filtered_files.append(x)
    return filtered_files


def main():
    files = get_files()
    fields = ['user', 'message', 'f_name']
    with open('output.json', 'w') as jsonfile:
        # writer = csv.DictWriter(csvfile, fieldnames=fields)
        # writer.writeheader()
        for f in files:
            data = parse_file(f)
            # writer.writerows(data)
            for d in data:
                write_json(jsonfile, d)


if __name__ == '__main__':
    main()
