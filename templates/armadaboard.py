# -- coding: utf-8 --
import re
# import locale
import dateutil.parser as dparser

from .base_template import BaseTemplate


class ArmadaboardParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "armadaboard"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//tr[td[contains(@class, "mobiletopic avatar")]]'
        self.header_xpath = '//tr[td[contains(@class, "mobiletopic avatar")]]'
        self.date_xpath = './/td[@class="desktop768"]//span[@class="postdetails"]//text()'
        self.title_xpath = '//a[@class="maintitle"]//text()'
        self.post_text_xpath = './/span[@class="postbody"]//text()'
        self.avatar_xpath = './/td[contains(@class, "avatar")]//table[2]//td//img/@src'
        self.author_xpath = './/td[contains(@class, "avatar")]//span[@class="name"]//text()'
        self.index = 1

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
            date_blocks = ' '.join(date_block)
            date = date_blocks.strip()
            date = date.replace('Добавлено:', '').strip()
            date = ' '.join(date.split(' ')[1:])
        else:
            return None

        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except Exception:
            return ""

        return ""
