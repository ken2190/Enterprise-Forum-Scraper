# -- coding: utf-8 --
import re
# import locale
import dateutil.parser as dparser

from .base_template import BaseTemplate


class Bbs2ctoParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "bbs.2cto.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@class="read_t"]'
        self.header_xpath = '//div[@class="read_t"]'
        self.title_xpath = '//h1[@id="subject_tpc"]//text()[1]'
        self.author_xpath = './/div[contains(@class,"readName")]/a//text()'
        self.post_text_xpath = './/div[contains(@class,"tpc_content")]//text()'
        self.avatar_xpath = './/a[contains(@class,"userCard")]/img/@src'
        self.mode = 'r'

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
                './/div[contains(@class,"tipTop")]/span[2]//text()'
            )[0].split(':')[-1]

        date = date_block.strip() if date_block else ""
        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except Exception:
            return ""

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(
            './/div[contains(@class,"tipTop")]/a//text()'
        )
        if not comment_block:
            comment_block = tag.xpath(
                './/div[contains(@class,"tipTop")]/span/a//text()'
            )

        if comment_block:
            comment_id = comment_block[0].strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')
