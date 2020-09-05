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
        self.date_xpath = './/span[@class="post_date"]/text()'
        self.title_xpath = '//td[@class="thead"]/div/strong/text()'
        self.post_text_xpath = './/div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = './/div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = '..//div[@class="post_head"]/div/strong/a/text()'
        self.author_xpath = './/div[@class="author_information"]//a/text()'

        # main function
        self.main()
