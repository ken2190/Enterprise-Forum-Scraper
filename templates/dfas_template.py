# -- coding: utf-8 --
import re
# import locale
import dateutil.parser as dparser

from .base_template import BaseTemplate


class DfasParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "annxjgfo6xo4igamx5sbeiocimkdqrjux5ga27smny6vdx4dgzn2wcqd.onion"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="brdmain"]/div[contains(@class,"blockpost")]'
        self.header_xpath = '//div[@id="brdmain"]/div[contains(@class,"blockpost")]'
        self.date_xpath = './/h2//span[@class="conr"]/following-sibling::a[1]/text()'
        self.author_xpath = './/dt/strong/a/span/text()'
        self.title_xpath = './/div[@class="postright"]/h3/text()'
        self.post_text_xpath = './/div[@class="postmsg"]/*/text()'
        self.avatar_xpath = './/div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = './/h2//span[@class="conr"]/text()'

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
        date = date_block[0].strip() if date_block else ""
        date = '2019 ' + date
        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except Exception:
            return ""
        return ""
