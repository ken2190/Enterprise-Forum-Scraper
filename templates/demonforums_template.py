# -- coding: utf-8 --
import re
import traceback
# import locale

from .base_template import BaseTemplate


class DemonForumsParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "demonforums.net"
        self.thread_name_pattern = re.compile(
            r'(.*)-\d+\.html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="posts"]/div[contains(@class, "posbit_classic")]'
        self.header_xpath = '//div[@id="posts"]/div[contains(@class, "posbit_classic")]'
        self.date_xpath = './/span[@class="post_date"]/text()'
        self.author_xpath = './/div[@class="profilelink_postbit"]/span/descendant::text()'
        self.title_xpath = '//div[@class="showthread_titlle wrapped"]/div/text()[1]'
        self.post_text_xpath =  './/div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = './/div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = './/div[@class="float_right posturl_post"]/strong/a/text()'

        # main function
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
            key=lambda x: (self.thread_name_pattern.search(x).group(1),
                           self.pagination_pattern.search(x).group(1)))

        return sorted_files
