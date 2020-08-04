# -- coding: utf-8 --
import re
import traceback
import utils
import dateutil.parser as dparser

from .base_template import BaseTemplate, BrokenPage


class AlphaBayParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "alphabay"
        self.thread_name_pattern = re.compile(
            r'(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.author_xpath = '//p[contains(text(), "Sold by")]/a/text()'
        self.date_xpath = '//text()[contains(.,"sold since")]/following-sibling::i[1]/text()'
        # main function
        self.main()

    def main(self):
        comments = []
        output_file = None
        for index, template in enumerate(self.files):
            print(template)
            try:
                html_response = utils.get_html_response(template)
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern.findall(file_name_only)
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
            except Exception:
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
        subject = html_response.xpath(
            '//div[@class="content2"]/div/h1[@class="std"]/text()')
        if subject:
            data.update({
                'subject': subject[0].strip()
            })

        author = html_response.xpath(self.author_xpath)
        if author:
            data.update({
                'author': author[0].strip()
            })

        date = html_response.xpath(self.date_xpath)
        if date:
            data.update({
                'date': str(dparser.parse(date[0].strip()).timestamp())
            })

        description_block = html_response.xpath(
            '//h2[text()="Product Description"]/following-sibling::p[1]')

        message = "\n".join([
            m.xpath('string()') for m in description_block
        ])
        if message:
            data.update({
                'message': message.strip()
            })

        return data
