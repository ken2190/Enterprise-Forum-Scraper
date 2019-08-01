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
        self.file_pattern = re.compile(
            r'-history\.html$'
        )
        self.output_file = '{}/USER_HISTORY.json'.format(
            str(output_folder)
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
        with open(self.output_file, 'w', encoding='utf-8') as fp:
            for index, template in enumerate(self.files):
                print(template)
                try:
                    html_response = utils.get_html_response(template)
                    user_id = get_user_id(html_response)
                    if not user_id:
                        continue
                    aliases = get_aliases(html_response)
                    self.write_data(fp, user_id, aliases)
                except Exception as ex:
                    traceback.print_exc()
                    continue
        print('\nJson written in {}'.format(self.output_file))
        print('----------------------------------------------------\n')

    def write_data(self, fp, user_id, aliases):
        data = {
            "_type": "forums",
            "_source": {
                "forum": "raidforums.com",
                "username": user_id,
                "aliases": aliases
            }
        }
        utils.write_json(fp, data)


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
