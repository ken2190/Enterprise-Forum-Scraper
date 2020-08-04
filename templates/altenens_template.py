# -- coding: utf-8 --
import re
# import locale
import dateutil.parser as dparser

from .base_template import BaseTemplate


class AltenensParser(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "altenens.org"
        self.thread_name_pattern = re.compile(
            r'(.*)-\d+\.html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//article[contains(@class,"message--post")]'
        self.author_xpath = './/div[@class="message-userDetails"]/h4/a//text()'
        self.post_text_xpath = './/article[contains(@class,"selectToQuote")]/descendant::text()[not(ancestor::blockquote)]'
        self.title_xpath = '//h1[@class="p-title-value"]//text()'
        self.comment_block_xpath = './/ul[contains(@class,"message-attribution-opposite")]/li/a//text()'
        self.header_xpath = '//article[contains(@class,"message--post")]'
        self.avatar_xpath = './/div[@class="message-avatar "]//img/@src'

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
        date_block = tag.xpath(
                './/time//text()'
            )[0].split('on')[-1]

        date = date_block.strip() if date_block else ""
        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except Exception:
            return ""

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        comment_block = ''.join(comment_block)

        if comment_block:
            comment_id = comment_block.strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')
