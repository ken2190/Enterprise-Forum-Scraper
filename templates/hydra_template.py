# -- coding: utf-8 --
import os
import re
from collections import OrderedDict
import traceback
import json
import utils
import datetime
import dateutil.parser as dparser
from lxml.html import fromstring


class BrokenPage(Exception):
    pass


class HydraParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = "hydraruzxpnew4af.onion"
        self.output_folder = output_folder
        self.thread_name_pattern = re.compile(
            r'(\d+)\.html$'
        )
        self.files = files
        self.folder_path = folder_path
        self.distinct_files = set()
        self.error_folder = "{}/Errors".format(output_folder)
        # main function
        self.main()

    def main(self):
        comments = []
        output_file = None
        for index, template in enumerate(self.files):
            print(template)
            try:
                html_response = utils.get_html_response(template, mode='r')
                pid = template.split('/')[-1].rsplit('.', 1)[0]
                self.process_page(pid, html_response)
            except BrokenPage as ex:
                utils.handle_error(
                    pid,
                    self.error_folder,
                    ex
                )
            except Exception:
                traceback.print_exc()
                continue

    def process_page(self, pid, html_response):
        data = {
            'forum': self.parser_name,
            'pid': pid
        }
        additional_data = self.extract_page_info(html_response)
        if not additional_data:
            return
        data.update(additional_data)
        final_data = {
            '_source': data
        }
        output_file = '{}/{}.json'.format(
            str(self.output_folder),
            pid
        )
        with open(output_file, 'w', encoding='utf-8') as file_pointer:
            utils.write_json(file_pointer, final_data)
            print('\nJson written in {}'.format(output_file))
            print('----------------------------------------\n')

    def extract_page_info(self, html_response):
        data = dict()
        subject = html_response.xpath(
            '//h1[@class="title"]/text()')
        if subject:
            data.update({
                'subject': subject[0].strip()
            })
        author = html_response.xpath(
            '//div[@class="header_shop__info"]/h1/text()')
        if author:
            data.update({
                'author': author[0].strip()
            })

        description_block = html_response.xpath(
            '//div[@id="descriptionContent"]/descendant::text()')
        message = " ".join([
            desc.strip() for desc in description_block
        ])
        if message:
            data.update({
                'message': message.strip()
            })
        return data
