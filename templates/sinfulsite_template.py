# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class SinfulSiteParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "sinfulsite.com"
        self.thread_name_pattern = re.compile(
            r'(.*)-\d+\.html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[contains(@class,"anchor post")]'
        self.header_xpath = '//div[contains(@class,"anchor post")]'
        self.date_xpath = './/div[@class="time fullwidth"]/text()[1]'
        self.author_xpath = './/div[contains(@class,"authorbit")]/div[3]//text()'
        self.title_xpath = '//div[@class="marginmid"][1]/text()'
        self.post_text_xpath = './/div[contains(@class,"textcontent") or contains(@class,"post_body")]//descendant::text()[not(ancestor::div[@class="hidelock"])]'
        self.avatar_xpath = './/div[@class="author_avatar"]//img/@src'
        self.comment_block_xpath ='.//div[@class="time fullwidth"]/div[1]/a/text()'

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
