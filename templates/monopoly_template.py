# -- coding: utf-8 --
import re

from .base_template import MarketPlaceTemplate


class MonopolyParser(MarketPlaceTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "monopoly"
        self.avatar_name_pattern = re.compile(r'.*base64,/.*/(\w+)/')
        self.avatar_xpath = '//div[@class="card-body"]//a/img/@src'
        self.title_xpath = '//h5/text()'
        self.author_xpath = '//div[@class="row rating-desc"]/div[1]/a[1]/text()'
        self.post_text_xpath = '//textarea[@class="form-control"]/text()'
        self.avatar_ext = 'jpeg'
        # main function
        self.main()

