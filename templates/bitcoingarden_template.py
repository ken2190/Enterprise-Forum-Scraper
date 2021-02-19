# -- coding: utf-8 --
import re
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class BitcoinGardenParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "bitcoingarden.org"
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="forumposts"]//div[contains(@class,"windowbg") and not(@valign)]'
        self.header_xpath = '//div[@id="forumposts"]//div[contains(@class,"windowbg") and not(@valign)]'
        self.date_xpath = "string(//div[contains(@class,'keyinfo')]/div[@class='smalltext'])"
        self.date_pattern = '%B %d, %Y, %I:%M:%S %p'
        self.author_xpath = './/div[@class="poster"]//a/text()'
        self.title_xpath = '//h3[@class="catbg"]/text()'
        self.post_text_xpath =  '//div[@class="post"]//text()'
        self.avatar_xpath = '//img[@class="avatar"]/@src'
        self.comment_block_xpath = 'div//div[@class="postarea"]//div[@class="smalltext"]/strong/text()'

        # main function
        self.main()

    def get_date(self, tag):
        post_date = tag.xpath(self.date_xpath)
        # Check thread date validation
        if not post_date:
            return

        post_date = post_date.strip().strip("»").strip("«").split("on:")[1]
        # Standardize
        post_date = post_date.strip()

        post_date = dparser.parse(post_date).timestamp()
        return str(post_date)

    def get_comment_id(self, tag):
        commentID = tag.xpath(self.comment_block_xpath)

        if commentID:
            comment_pattern = re.compile(r'Reply #(\d+) on:')
            match = comment_pattern.findall(commentID[0])
            commentID = match[0] if match else ""

        return commentID.replace(',', '')