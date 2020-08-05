# -- coding: utf-8 --
import re
import traceback
import utils

from .base_template import BaseTemplate, BrokenPage


class DarkbayParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "darkbayupenqdqvv.onion"
        self.thread_name_pattern = re.compile(
            r'(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = kwargs.get('files')

        # main function
        self.main()

    def main(self):
        comments = []
        output_file = None
        for index, template in enumerate(self.files):
            print(template)
            try:
                html_response = utils.get_html_response(template)
                pid = template.split('/')[-1].rsplit('.', 1)[0]
                pid = str(
                    int.from_bytes(
                        pid.encode('utf-8'),
                        byteorder='big'
                    ) % (10 ** 7)
                )
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
            '//body/div[1]//div[@class="row"][1]/div[2]/h4//text()')
        subject = ''.join(subject).strip()
        if subject:
            data.update({
                'subject': subject
            })
        author = html_response.xpath(
            '//div[@class="card-body"]/div[1]/a//text()')
        author = ''.join(author).strip()
        if author:
            data.update({
                'author': author
            })

        description_block = html_response.xpath(
            '//div[@class="mt-4"]//p//text()')
        message = " ".join(description_block).strip()
        if message:
            data.update({
                'message': message.strip()
            })

        return data
