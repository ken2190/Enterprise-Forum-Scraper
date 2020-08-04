# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class TorigonParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "torigon"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.index = 1
        self.mode = 'r'
        self.comments_xpath = '//div[contains(@class,"post ")]'
        self.header_xpath = '//div[contains(@class,"post ")]'
        self.date_xpath = './/p[@class="author"]/text()[3]'
        self.author_xpath = './/p[@class="author"]//span[contains(@class,"username")]/text()'
        self.post_text_xpath = './/div[@class="content"]//text()'
        self.avatar_xpath = './/img[@class="avatar"]/@src'
        self.title_xpath = '//h2[@class="topic-title"]//text()'

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

    def get_avatar(self, tag):
        avatar_block = tag.xpath(self.avatar_xpath)
        if not avatar_block:
            return ""

        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""

        if name_match[0].startswith('svg'):
            return ""

        return name_match[0]

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = title[0].strip().split(']')[-1] if title else None

        return title
