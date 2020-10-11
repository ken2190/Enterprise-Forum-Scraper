# -- coding: utf-8 --
import re

from .base_template import MarketPlaceTemplate


class WhiteHouseMarketParser(MarketPlaceTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "whitehousemarket"
        self.avatar_name_pattern = re.compile(r'.*base64,/.*/(\w+)/')
        self.avatar_xpath = '//div[@class="panel-body"]//img/@src'
        self.title_xpath = '//div[contains(@class,"panel-heading")]/strong/text()'
        self.author_xpath = '//p[contains(@class, "alert alert-info")]/strong/a/text()'
        self.post_text_xpath = ' //div[contains(@class,"panel-body")][textarea]//textarea/text()[1]'
        self.avatar_ext = 'jpeg'

        self.main()
