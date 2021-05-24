# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class OgUsersParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "ogusers.com"
        self.avatar_name_pattern = re.compile(r".*avatar_(\d+\.\w+)\?")
        self.mode = 'r'
        self.comments_xpath = '//div[@class="postbox"]'
        self.header_xpath = '//div[@class="postbox"]'
        self.date_xpath = './/div//div[contains(@class,"pb_date")]/span/@title' \
                          '|div//div[contains(@class,"pb_date")]/text()'
        self.title_xpath = '//span[@class="showthreadtopbar_size"]/text()'
        self.post_text_xpath = './/div//div[@class="post_body scaleimages"]' \
                               '/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = './/aside//div[@class="postbit-avatar"]/a/img/@src|.//img[@class="profileshow"]/@src'
        self.comment_block_xpath = './/div//div[@class="float_right postbitnum"]/strong/a/text()'
        self.author_xpath = './/aside//div[contains(@class,"postbitdetail")]/span//text()'
        self.offset_hours = 3
        self.date_pattern = "%m-%d-%Y, %I:%M %p"

        # main function
        self.main()

    @staticmethod
    def construct_date_string(date_block):
        date_str = ""
        for date in date_block:
            date = date.strip()
            if date:
                date_str += date
        return date_str

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date_string = self.construct_date_string(date_block)
        date = self.parse_date_string(date_string)
        return date
