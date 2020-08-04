# -- coding: utf-8 --
import re
import traceback
# import locale
import utils
import dateparser

from .base_template import BaseTemplate


class DelfcodeParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "delfcode.ru"
        self.thread_name_pattern = re.compile(
            r'(.*)-\d+\.html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.mode = 'r'
        self.comments_xpath = '//table[@class="gTable"]/tr[contains(@id,"post")]'
        self.header_xpath = '//table[@class="gTable"]/tr[contains(@id,"post")]'
        self.title_xpath = '//a[@class="forumBarA"][1]/text()[1]'
        self.date_xpath = './/td[@class="postTdTop"][2]/text()'
        self.author_xpath = './/td[@class="postTdTop"][1]/a/text()'
        self.post_text_xpath = './/td[@class="posttdMessage"]/span//text()'
        self.avatar_xpath = './/td[@class="postTdInfo"]/img[@class="userAvatar"]/@src'
        self.comment_block_xpath = './/td[@class="postTdTop"][2]/a/text()'

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

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = ''.join(date_block)
        date = date.split(' ')[1:4]
        date = ' '.join(date)
        try:
            date = dateparser.parse(date).timestamp()
            return str(date)
        except Exception:
            return ""
