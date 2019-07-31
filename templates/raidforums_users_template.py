# -- coding: utf-8 --
import os
import re
import traceback
import json
import datetime
import utils
import dateutil.parser as dparser


class RaidForumsUserParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = parser_name
        self.output_folder = output_folder
        self.file_pattern = re.compile(
            r'-history\.html$'
        )
        self.files = self.get_filtered_files(files)
        self.folder_path = folder_path
        self.main()

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.file_pattern.search(
                    x.split('/')[-1]) is not None,
                files
            )
        )
        return filtered_files

    def main(self):
        comments = []
        for index, template in enumerate(self.files):
            print(template)
            try:
                html_response = utils.get_html_response(template)
                user_id = get_user_id(html_response)
                if not user_id:
                    continue
                aliases = get_aliases(html_response)
                self.write_data(user_id, aliases)
            except Exception as ex:
                traceback.print_exc()
                continue

    def write_data(self, user_id, aliases):
        output_file = '{}/{}.json'.format(
            str(self.output_folder),
            user_id
        )
        with open(output_file, 'w', encoding='utf-8') as fp:
            for alias in aliases:
                alias.update({
                    'user_id': user_id
                })
                utils.write_json(fp, alias)
        print('\nJson written in {}'.format(output_file))
        print('----------------------------------------------------\n')


def get_user_id(html_response):
    user_id = html_response.xpath(
        '//strong[contains(text(), "Username History for")]/text()')
    if not user_id:
        return
    match = re.findall(r'.*for (.*)', user_id[0])
    return match[0] if match else None


def get_aliases(html_response):
    aliases = list()
    rows = html_response.xpath('//tr[td[contains(@class, "trow")]]')
    for row in rows:
        alias, date_changed = row.xpath('td/text()')
        ts = dparser.parse(date_changed.strip()).timestamp()
        aliases.append({
            'alias': alias,
            'date_changed': str(ts)
        })
    return aliases
