# -- coding: utf-8 --
import datetime
import traceback

import dateutil.parser as dparser
import utils
import re
from .base_template import BaseTemplate

class BrokenPage(Exception):
    pass


class V3RMillionParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "v3rmillion.net"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//div[@id="posts"]/div[@class="post "]'
        self.header_xpath = '//div[@id="posts"]/div[@class="post "]'
        self.date_xpath = 'div//span[@class="post_date"]/text()'
        self.date_pattern = "%m-%d-%Y, %I:%M %p"
        self.title_xpath = '//span[@class="active"]/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = 'div[@class="post_head"]/div/strong/a/text()'
        self.author_xpath = 'div//div[@class="author_information"]/strong//text()'

        # main function
        self.main()

