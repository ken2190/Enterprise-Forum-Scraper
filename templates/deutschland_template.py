# -- coding: utf-8 --
import re
# import locale
import traceback
import utils
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class DeutschlandParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "deutschland"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//div[@id="posts"]/div[@class="post "]'
        self.header_xpath = '//div[@id="posts"]/div[@class="post "]'
        self.date_xpath_1 = './/span[@class="post_date"]/text()'
        self.date_xpath_2 = './/span[@class="post_date"]/span[@title]/@title'
        self.title_xpath = '//td[@class="thead"]/div/strong/text()'
        self.post_text_xpath = './/div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = './/div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = '..//div[@class="post_head"]/div/strong/a/text()'
        self.author_xpath = './/div[@class="author_information"]//a/text()'
        self.date_pattern = "%d-%m-%Y, %H:%M"
        self.offset_hours = -2

        # main function
        self.main()

    def construct_date_string(self, tag):
        date_block = tag.xpath(self.date_xpath_1)
        date_string = date_block[0].strip() if date_block else None

        if date_string and date_string.startswith(", "):
            date_block2 = tag.xpath(self.date_xpath_2)
            date_string2 = date_block2[0].strip() if date_block2 else None
            date_string = date_string2 + date_string
        return date_string

    def get_date(self, tag):
        date_string = self.construct_date_string(tag)
        date = self.parse_date_string(date_string)
        return date
