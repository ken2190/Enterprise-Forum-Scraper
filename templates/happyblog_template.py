# -- coding: utf-8 --
import re
# import locale
import dateutil.parser as dparser
import utils

from .base_template import BaseTemplate


class HappyblogParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "happyblog"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.output_folder = kwargs.get('output_folder')

        # main function
        self.main()

    def get_filtered_files(self, files):
        sorted_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(x) is not None,
                files
            )
        )

        return sorted_files
    
    def main(self):
        comments = []
        output_file = None

        for index, template in enumerate(self.files):
            html_response = self.get_html_response(template)
            file_name_only = template.split('/')[-1]
            match = self.thread_name_pattern.findall(file_name_only)

            if not match:
                continue

            self.thread_id = match[0]

            pid = self.get_pid()
            output_file = '{}/{}.json'.format(
                str(self.output_folder),
                pid
            )
            file_pointer = open(output_file, 'w', encoding='utf-8')

            posts = html_response.xpath("//div[contains(@id, 'post_')]")
            
            for post in posts:
                pid = post.xpath('./@data-id')[0]
                title = post.xpath("//h2[@class='blog-post-title']/text()")[0]

                author = 'Revil Happyblog'
                images = post.xpath('//img[@class="item-image"]/@src')
                images = set(images)
                images = [image.split('/')[-1] for image in images ]

                comments = post.xpath("//div[@class='item-body']//text()")
                message = ' '.join(comments)
                
                data = {
                    '_source': {
                        'forum': 'happyblog',
                        'pid': pid,
                        'subject': title,
                        'author': author,
                        'message': message,
                        'images': images
                    }
                }
                utils.write_json(file_pointer, data)

                print('\nJson written in {}'.format(output_file))
                print('----------------------------------------\n')
