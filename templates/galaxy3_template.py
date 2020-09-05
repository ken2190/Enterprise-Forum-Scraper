# -- coding: utf-8 --
import re
from .base_template import BaseTemplate


class Galaxy3Parser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = 'galaxy3'
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.comments_xpath = '//div[@class="elgg-main elgg-body"]/ul[@class="elgg-list elgg-list-entity"]/li'
        self.header_xpath = '//div[@class="elgg-main elgg-body"]/ul[@class="elgg-list elgg-list-entity"]/li'
        self.date_xpath = 'div//div[@class="elgg-listing-summary-subtitle elgg-subtext"]/time/@title'
        self.title_xpath = '//*[@class="elgg-heading-main"]/text()'
        self.post_text_xpath = 'div//div[@class="elgg-listing-summary-content elgg-content"]/descendant::text()'
        self.avatar_xpath = 'div[@class="elgg-image-block clearfix thewire-post"]//img/@src'
        self.author_xpath = './/div//div[@class="elgg-listing-summary-subtitle elgg-subtext"]/a/text()'
        self.index = 1

        # main function
        self.main()
