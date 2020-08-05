# -- coding: utf-8 --
import re
import traceback
import utils

from .base_template import BaseTemplate, BrokenPage


class HydraParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "hydraruzxpnew4af.onion"
        self.thread_name_pattern = re.compile(
            r'(\d+)\.html$'
        )
        self.files = kwargs.get('files')
        self.mode = 'r'

        # main function
        self.main()

    def main(self):
        comments = []
        output_file = None
        for index, template in enumerate(self.files):
            print(template)
            try:
                html_response = self.get_html_response(template)
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
