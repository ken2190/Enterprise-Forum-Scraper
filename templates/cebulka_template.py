# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class CebulkaParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "http://cebulka7uxchnbpvmqapg5pfos4ngaxglsktzvha7a5rigndghvadeyd.onion"
        self.thread_name_pattern = re.compile(
            r'(.*)-\d+\.html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="forum1"]/div[contains(@class, "post ")]'
        self.header_xpath = '//div[@id="forum1"]/div[contains(@class, "post ")]'
        self.title_xpath = '//span[contains(@class,"crumblast")]/text()'
        self.date_xpath = './/span[@class="post_date"]/text()'
        self.author_xpath = './/span[contains(@class,"post-byline")]/a/text()'
        self.post_text_xpath = './/div[contains(@class,"post-entry")]/descendant::text()[not(ancestor::div[@class="quotebox"])]'
        self.comment_block_xpath = './/div[@class="posthead"]//span[@class="post-num"]/text()'
        self.avatar_xpath = './/li[@class="useravatar"]//img/@src'

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
