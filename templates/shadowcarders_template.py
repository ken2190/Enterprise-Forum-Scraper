# -- coding: utf-8 --
import os
import re
from collections import OrderedDict
import traceback
import json
import utils
import datetime
import dateparser
from lxml.html import fromstring


from .base_template import BaseTemplate


class ShadowCardersParser(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "shadowcarders.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html'
        )
        self. avatar_name_pattern = re.compile(r".*/(\S+\.\w+)")
        # self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//ol[@class="messageList"]/li'
        self.header_xpath = '//ol[@class="messageList"]/li'
        self.date_xpath = 'div//a[@class="datePermalink"]/span/text()'
        self.author_xpath = './/h3//a[@class="username"]//text()'
        self.title_xpath = '//div[@class="titleBar"]/h1/text()'
        self.post_text_xpath = 'div//blockquote[contains(@class,"messageText")]//text()'
        self.comment_block_xpath = './/div[@class="publicControls"]/a/text()'
        self.avatar_xpath = './/a[@data-avatarhtml="true"]/img/@src'
        self.comment_id = ""
        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = date_block[0].strip() if date_block else None

        if not date:
            return ""

        try:
            date = dateparser.parse(date).timestamp()
            return str(date)
        except:
            pass

        return ""
