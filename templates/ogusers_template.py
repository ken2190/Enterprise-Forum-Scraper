# -- coding: utf-8 --
import re
import dateutil.parser as dparser

from .base_template import BaseTemplate


class OgUsersParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "ogusers.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.mode = 'r'
        self.comments_xpath = '//div[@class="postbox"]'
        self.header_xpath = '//div[@class="postbox"]'
        self.date_xpath = 'div//div[@class="inline pb_date smalltext"]/span/@title'
        self.title_xpath = '//span[@class="showthreadtopbar_size"]/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'aside//div[@class="postbit-avatar"]/a/img/@src'
        self.comment_block_xpath = 'div//div[@class="float_right postbitnum"]/strong/a/text()'

        # main function
        self.main()

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(x) is not None,
                files
            )
        )
        sorted_files = sorted(
            filtered_files,
            key=lambda x: (
                int(self.thread_name_pattern.search(x).group(1)),
                int(self.pagination_pattern.search(x).group(1))
            ))

        return sorted_files

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        if not date_block:
            date_block = tag.xpath(
                'div//div[@class="inline pb_date smalltext"]/text()')

        date = date_block[0].strip() if date_block else ""
        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except Exception:
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            'aside//div[@class="postbitdetail"]/span/a/span/text()'
        )
        if not author:
            author = tag.xpath(
                'aside//div[@class="postbitdetail"]/span/a/text()')
        if not author:
            author = tag.xpath(
                'aside//div[@class="postbitdetail"]/span/a/font/text()')

        author = author[0].strip() if author else None
        return author

    def get_avatar(self, tag):
        avatar_block = tag.xpath(self.avatar_xpath)
        if not avatar_block:
            return ""

        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""

        return name_match[0] if 'svg' not in name_match[0] else ''
