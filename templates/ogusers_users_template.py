# -- coding: utf-8 --
import os
import re
import traceback
import json
import datetime
import utils
import dateutil.parser as dparser


class OgUsersUserParser:
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
                    user_info = get_user_info(html_response)
                    if not user_info:
                        continue
                    aliases = get_aliases(html_response)
                    if not aliases:
                        continue
                    self.write_data(fp, user_info[0], user_info[1], aliases)
                except Exception as ex:
                    traceback.print_exc()
                    continue
        print('\nJson written in {}'.format(self.output_file))
        print('----------------------------------------------------\n')

    def write_data(self, fp, uid, username, aliases):
        data = {
            "_type": "forums",
            "_source": {
                "forum": "ogusers.com",
                "uid": uid,
                "username": username,
                "aliases": aliases
            }
        }
        utils.write_json(fp, data)


def get_user_info(html_response):
    id_block = html_response.xpath('//a[@id="alerts "]/@onclick')
    if not id_block:
        return
    match = re.findall(r'uid%3D(\d+)', id_block[0])
    uid = match[0]
    username = html_response.xpath('//td[@class="thead"]/strong/a/text()')
    if not username:
        return
    return uid, username[0]


def get_aliases(html_response):
    aliases = list()
    if html_response.xpath('//td[text()="No changes are logged."]'):
        return
    rows = html_response.xpath('//tr[td[contains(@class, "trow")]]')
    for row in rows:
        alias, date_changed = row.xpath('td/text()')
        try:
            ts = str(dparser.parse(date_changed.strip()).timestamp())
        except Exception:
            ts = date_changed
        aliases.append({
            'alias': alias,
            'date_changed': ts
        })
    return aliases
