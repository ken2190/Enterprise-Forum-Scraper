# -- coding: utf-8 --
import re
import locale

from .base_template import BaseTemplate


class ProcrdParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        super().__init__(*args, **kwargs)
        self.parser_name = "procrd.me"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//article[contains(@class,"message--post")]'
        self.header_xpath = '//article[contains(@class,"message--post")]'
        self.title_xpath = '//h1[@class="p-title-value"]//text()'
        self.date_xpath = './/time/@datetime'
        self.author_xpath = './/div[@class="message-userDetails"]/h4/a//text()'
        self.post_text_xpath = './/article[contains(@class,"selectToQuote")]/descendant::text()[not(ancestor::div[contains(@class,"bbCodeBlock--quote")])]'
        self.avatar_xpath = './/div[@class="message-avatar "]//img/@src'
        self.comment_block_xpath = './/ul[contains(@class,"message-attribution-opposite")]/li[2]/a/text()'

        # main function
        self.main()
