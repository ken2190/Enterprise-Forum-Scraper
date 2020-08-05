# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class DarkSkiesParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = kwargs.get('parser_name')
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="posts"]/div[@class="post "]'
        self.header_xpath = '//div[@id="posts"]/div[@class="post "]'
        self.date_xpath = 'div//span[@class="post_date"]/text()'
        self.date_pattern = "%m-%d-%Y, %I:%M %p"
        self.title_xpath = '//td[@class="thead"]/div/strong/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = 'div//div[@class="post_head"]/div/strong/a/text()'

        # main function
        self.main()

    def get_author(self, tag):
        author = tag.xpath(
            'div//div[@class="author_information"]/strong/span/a/text()'
        )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]/strong//em/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]/strong//b/span/text()'
            )
        author = author[0].strip() if author else None
        return author
