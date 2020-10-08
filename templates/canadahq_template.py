# -- coding: utf-8 --
import re

from .base_template import MarketPlaceTemplate


class CanadaHQParser(MarketPlaceTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "canadahq.at"
        self.thread_name_pattern = re.compile(
            r'(\w+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.avatar_xpath = './/div[@class="panel-body"]//img/@src'
        self.title_xpath = '//div[@class="panel-heading"]/text()'
        self.author_xpath = '//span[contains(text(), "Sold by:")]/text()'
        self.post_text_xpath = '//div[@class="margin-top-25"]/descendant::text()'
        # main function
        self.main()

    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        return author[0].replace('Sold by:', '').strip()
