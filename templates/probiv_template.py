# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class ProbivParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "probiv.one"
        self.thread_name_pattern = re.compile(
            r'(.*)-\d+\.html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@class="message-inner"]'
        self.header_xpath = '//div[@class="message-inner"]'
        self.date_xpath = './/time/text()'
        self.author_xpath = './/span[contains(@class,"username")]/text()'
        self.title_xpath = '//h1[@class="p-title-value"]//text()'
        self.post_text_xpath = './/article[contains(@class,"message-body js-selectToQuote")]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = './/a[contains(@class, "avatar")]/img/@src'
        self.comment_block_xpath = './/ul[@class="message-attribution-opposite message-attribution-opposite--list"]/li[last()]/a/text()'

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
