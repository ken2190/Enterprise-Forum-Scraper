# -- coding: utf-8 --
import re
import traceback
# import locale
import utils

from .base_template import BaseTemplate


class OpenCardParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "opencard.us"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//article[contains(@class,"message--post")]'
        self.header_xpath = '//div'
        self.title_xpath = '//h1[@class="p-title-value"]//text()'
        self.date_xpath = './/time/@data-time'
        self.author_xpath = './/div[@class="message-userDetails"]/h4/a//text()'
        self.post_text_xpath = './/article[contains(@class,"selectToQuote")]/descendant::text()[not(ancestor::div[contains(@class,"bbCodeBlock--quote")])]'
        self.avatar_xpath = './/div[@class="message-avatar "]//img/@src'
        self.comment_block_xpath = './/ul[contains(@class,"message-attribution-opposite")]/li[3]/a/text()'

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

        if date_block:
            date = date_block[0]
            return str(date)
        else:
            return ""
