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


class AlphaBayParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = parser_name
        self.output_folder = output_folder
        self.thread_name_pattern_1 = re.compile(
            r'listing\.php.*id=(\d+)$'
        )
        self.thread_name_pattern_2 = re.compile(
            r'(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(files)
        self.folder_path = folder_path
        self.distinct_files = set()
        self.error_folder = "{}/Errors".format(output_folder)
        self.thread_id = None
        # main function
        self.main()

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern_1.search(x) is not None,
                files
            )
        )
        sorted_files_1 = sorted(
            filtered_files,
            key=lambda x: int(self.thread_name_pattern_1.search(x).group(1)))

        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern_2.search(x) is not None,
                files
            )
        )
        sorted_files_2 = sorted(
            filtered_files,
            key=lambda x: int(self.thread_name_pattern_2.search(x).group(1)))

        return sorted_files_1 + sorted_files_2

    def main(self):
        comments = []
        output_file = None
        for index, template in enumerate(self.files):
            print(template)
            try:
                html_response = utils.get_html_response(template)
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern_1.findall(file_name_only)
                if not match:
                    match = self.thread_name_pattern_2.findall(file_name_only)
                if not match:
                    continue
                pid = self.thread_id = match[0]
                self.process_page(pid, html_response)
            except BrokenPage as ex:
                utils.handle_error(
                    pid,
                    self.error_folder,
                    ex
                )
            except:
                traceback.print_exc()
                continue

    def process_page(self, pid, html_response):
        data = ({
            'pid': pid
        })
        additional_data = self.extract_page_info(html_response)
        if not additional_data:
            return
        data.update(additional_data)
        output_file = '{}/{}.json'.format(
            str(self.output_folder),
            pid
        )
        with open(output_file, 'w', encoding='utf-8') as file_pointer:
            utils.write_json(file_pointer, data)
            print('\nJson written in {}'.format(output_file))
            print('----------------------------------------\n')

    def extract_page_info(self, html_response):
        data = dict()
        title = html_response.xpath(
            '//div[@class="content2"]/div/h1[@class="std"]/text()')
        if title:
            data.update({
                'title': title[0].strip()
            })
        seller = html_response.xpath(
            '//p[contains(text(), "Sold by")]/a/text()')
        if seller:
            data.update({
                'seller': seller[0].strip()
            })

        date = html_response.xpath(
            '//p[contains(string(), "sold since")]/i/text()')
        if date:
            data.update({
                'date': date[-1].strip()
            })
        description_block = html_response.xpath(
            '//h2[text()="Product Description"]/following-sibling::p[1]')
        description = "\n".join([
            description.xpath('string()') for description in description_block
        ])
        if description:
            data.update({
                'description': description.strip()
            })
        return data
