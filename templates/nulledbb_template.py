# -- coding: utf-8 --
import re
import dateutil.parser as dparser

from .base_template import BaseTemplate


class NulledBBParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "nulledbb.com"
        # self.thread_name_pattern = re.compile(
            # r'(.*)-\d+\.html$'
        # )
        self.thread_name_pattern = re.compile(
            r'(\d+)-\d+\.html$'
        )
        self.pagination_pattern = re.compile(
            r'-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@class="wrapper"]/div[1][@class="table-wrap"]'
        self.header_xpath = '//div[@class="wrapper"]/div[1][@class="table-wrap"]'
        self.date_xpath = 'div//div[contains(string(), "Posted:")]/text()'
        self.title_xpath = '//div[@class="table-wrap"]//h1/text()'
        self.post_text_xpath = 'div//div[@class="postbit-message-content"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = 'div//div[@class="right"]/strong/a/text()'

        # main function
        self.main()

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(
                    x.split('/')[-1]) is not None,
                files
            )
        )
        sorted_files = sorted(
            filtered_files,
            key=lambda x: int(self.thread_name_pattern.search(
                x.split('/')[-1]).group(1)))

        return sorted_files

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = [d.strip() for d in date_block if d.strip()]
        if not date:
            return

        date = date[0].replace('Posted:', '').strip()
        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except:
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            'div//div[contains(@class, "postbit-username")]//span/text()'
        )
        if not author:
            author = tag.xpath(
                'div//div[contains(@class, "postbit-username")]//span/s/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="message-userDetails"]/h4/a/text()'
            )

        author = author[0].strip() if author else None
        return author

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        if comment_block:
            comment_id = comment_block[-1].split('#')[-1]

        return comment_id.replace(',', '').strip()
