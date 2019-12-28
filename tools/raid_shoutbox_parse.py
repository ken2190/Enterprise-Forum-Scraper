import re
import json
import os
import csv
import argparse

from lxml.html import fromstring
from lxml.etree import ParserError
from glob import glob


PATH = '/Users/umeshpathak/Downloads/RF_LOGS'


def parse_file(f):
    value = re.findall(r'\((\d+_\d+)\)', f)[0]
    with open(f, 'r', encoding="utf-8") as fp:
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


def get_files(folder_path):
    files = []
    for file in glob("%s/*" % folder_path):
        if os.path.isfile(file):
            files.append(file)

    pattern = re.compile(
        r'log\((\d+)_\d+\)',
        re.IGNORECASE
    )

    sorted_files = sorted(
        files,
        key=lambda x: int(pattern.search(x).group(1))
    )

    filtered_files = list()
    seen = set()

    for x in sorted_files:
        value = re.findall(
            r'\((\d+_\d+)\)',
            x
        )[0]
        if value not in seen:
            seen.add(value)
            filtered_files.append(x)

    return filtered_files


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Shoutbox Parser Tools"
    )
    parser.add_argument(
        "-i", "--input",
        help="Input folder path",
        required=True
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file, json or csv",
        required=True
    )
    parser.add_argument(
        "-f", "--field",
        help="Field to process, seperate by comma",
        required=False
    )

    return {
        key: value for key, value in
        parser.parse_args()._get_kwargs()
    }


def main():
    kwargs = parse_arguments()
    input_path = kwargs.get("input")
    output_path = kwargs.get("output")
    files = get_files(input_path)

    if ("csv" not in output_path.lower()
            and "json" not in output_path):
        raise ValueError(
            "Output file must be either csv or json"
        )

    if "json" in output_path.lower():
        with open(output_path, 'w', encoding="utf-8") as json_file:
            for f in files:
                data = parse_file(f)
                for d in data:
                    write_json(json_file, d)


if __name__ == '__main__':
    main()
