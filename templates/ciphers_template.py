# -- coding: utf-8 --
import re
# import locale
import dateutil.parser as dparser

from .base_template import BaseTemplate


class CiphersParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "ciphers.pw"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//article[contains(@class,"message--post")]'
        self.header_xpath = '//article[contains(@class,"message--post")]'
        self.title_xpath = '//h1[@class="p-title-value"]//text()'
        self.date_xpath = 'div//div[@class="message-attribution-main"]/a/time/@data-time'
        self.author_xpath = './/div[@class="message-userDetails"]/h4[@class="message-name"]/descendant::text()'
        self.post_text_xpath = './/article[contains(@class,"selectToQuote")]/descendant::text()[not(ancestor::div[contains(@class,"bbCodeBlock--quote")])]'
        self.comment_block_xpath = './/ul[contains(@class,"message-attribution-opposite")]/li[2]/a/text()'

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
        avatar_block = tag.xpath(
            './/div[@class="message-avatar-wrapper"]/a/@data-user-id'
        )
        if not avatar_block:
            return ""

        return avatar_block[0] + '.jpg'
