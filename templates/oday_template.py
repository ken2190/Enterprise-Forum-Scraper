# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class OdayParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "0day.su"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="posts"]/table'
        self.header_xpath = '//div[@id="posts"]/table'
        self.date_xpath = 'tr[2]//td/span[@class="smalltext"]/text()'
        self.date_pattern = "%m-%d-%Y"
        self.title_xpath = '//td[@class="thead"]/div/strong/text()'
        self.post_text_xpath = 'tr[1]/td[2]/table//div[@class="post_body"]/descendant::text()[not(ancestor::blockquote)]'
        self.comment_block_xpath = 'tr[1]/td[2]/table//strong[contains(text(), "Post:")]/a/text()'
        self.avatar_xpath = 'tr[1]//td//span[@class="smalltext"]/a/img/@src'

        # main function
        self.main()

    def get_author(self, tag):
        author = tag.xpath(
            'tr[1]//td/strong/a/text()'
        )
        if not author:
            author = tag.xpath(
                'tr[1]//td/strong/span/text()'
            )
        if not author:
            author = tag.xpath(
                'tr[1]//td/strong/span/a/span/text()'
            )
        if not author:
            author = tag.xpath(
                'tr[1]//td/strong/span/a//text()'
            )
        if not author:
            author = tag.xpath(
                'tr[1]//td/strong/span//s/text()'
            )
        author = author[0].strip() if author else None
        return author
