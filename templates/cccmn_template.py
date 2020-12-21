# -- coding: utf-8 --
import re
import utils

from .base_template import BaseTemplate


class CccmnParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "ccc.mn"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.index = 1
        self.comments_xpath = '//article[contains(@id, "elComment_")]'
        self.header_xpath = '//article[contains(@id, "elComment_")]'
        self.date_xpath = './/time/@title'
        self.author_xpath = 'aside//a[@class="ipsType_break"]//text()|aside//strong[@itemprop="name"]//text()|aside//strong/text()'
        self.title_xpath = '//div[@class="ipsType_break ipsContained"]/span/text()'
        self.post_text_xpath = 'div//div[@data-role="commentContent"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'aside//li[@class="cAuthorPane_photo"]/a/img/@src'
        self.mode = 'r'

        # main function
        self.main()
