# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class MctradesParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "mctrades.org"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.title_xpath = '//div[contains(@class,"titleBar")]//h1/text()'
        self.comments_xpath = '//ol[@class="messageList"]/li[contains(@class,"message")]'
        self.header_xpath = '//ol[@class="messageList"]/li[contains(@class,"message")]'
        self.date_xpath = './/div[@class="messageDetails"]' \
                          '//abbr[@class="DateTime"]/@data-time|' \
                          './/div[@class="messageDetails"]'\
                          '//span[@class="DateTime"]/@title'
        self.author_xpath = './/div[contains(@class,"messageUserInfo")]' \
                            '//div[contains(@class,"uix_userTextInner")]/a//text()'
        self.post_text_xpath = './/div[contains(@class,"messageContent")]' \
                               '//article/blockquote/descendant::text()[not(ancestor::div[contains(@class,"bbCodeQuote")])]'
        self.avatar_xpath = './/div[contains(@class,"avatarHolder")]//img/@src'
        self.comment_block_xpath = './/div[@class="messageDetails"]/a//text()'
        self.offset_hours = 7
        self.date_pattern = '%b %d, %Y at %I:%M %p'
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
            key=lambda x: (self.thread_name_pattern.search(x).group(1),
                           self.pagination_pattern.search(x).group(1)))

        return sorted_files

    def get_avatar(self, tag):
        avatar_block = tag.xpath(self.avatar_xpath)
        if not avatar_block:
            return ""

        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""

        if name_match[0].startswith('svg'):
            return ""

        return name_match[0]

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = title[0].strip().split(']')[-1] if title else None

        return title

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        if comment_block:
            comment_id = comment_block[-1].strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date_string = date_block[0].strip() if date_block else None
        date = self.parse_date_string(date_string)
        return date
