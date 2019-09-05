# -- coding: utf-8 --
import os
import re
from collections import OrderedDict
import traceback
import json
import utils
import datetime
from lxml.html import fromstring


class BrokenPage(Exception):
    pass


class NulledToBanListParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = parser_name
        self.output_folder = output_folder
        self.thread_name_pattern = re.compile(
            r'page-(\d+).*html$'
        )
        self.output_file = '{}/banlist.json'.format(self.output_folder)
        self.files = self.get_filtered_files(files)
        self.folder_path = folder_path
        self.main()

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(x) is not None,
                files
            )
        )
        sorted_files = sorted(
            filtered_files,
            key=lambda x: int(self.thread_name_pattern.search(x).group(1)))

        return sorted_files

    def main(self):
        comments = []
        with open(self.output_file, 'w', encoding='utf-8') as file_pointer:
            for index, template in enumerate(self.files):
                print(template)
                try:
                    html_response = utils.get_html_response(template)
                    data = self.extract_user_details(html_response)
                    for d in data:
                        # write file
                        utils.write_json(file_pointer, d)
                    print('Done...!')
                except Exception:
                    traceback.print_exc()
                    continue

    def extract_user_details(self, response):
        rows = response.xpath(
            '//tbody[@class="ban-tbody"]/tr'
        )
        data = list()
        for row in rows:
            username = row.xpath('td[1]//span/s/text()')[0]
            reason_block = row.xpath('td[2]/text()')[0]
            reason, ip = reason_block.split('|')
            email = row.xpath(
                'td[2]/a[@class="__cf_email__"]/@data-cfemail')[0]
            decoded_email = utils.get_decoded_email(email)
            data.append({
                'username': username.strip(),
                'reason': reason.strip(),
                'ip': ip.replace('-', '').strip(),
                'email': decoded_email
            })
        return data


        return comment_id.replace(',', '')
