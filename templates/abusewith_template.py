# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class AbuseWithParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "abusewith.us"
        self.thread_name_pattern = re.compile(
            r'showthread.*?tid=(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'page=(\d+).html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[contains(@class,"post classic")]'
        self.header_xpath = '//div[contains(@class,"post classic")]'
        self.date_xpath = 'div//span[@class="post_date"]/text()'
        self.author_xpath = 'div//div[@class="author_information"]/span//span[@class="largetext"]/descendant::text()'
        self.title_xpath = '//td[@class="thead"]/div/strong/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.comment_block_xpath = 'div//div[@class="post_head"]//strong/a/text()'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'
        self.avatar_ext = 'jpg'

        # main function
        self.main()

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        if comment_block:
            comment_id = comment_block[-1].strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')
