# -- coding: utf-8 --
import re
import locale
import datetime

from .base_template import BaseTemplate


class BadKarmaParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        super().__init__(*args, **kwargs)
        self.parser_name = "bezlica.top (badkarma)"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[contains(@class, "uix_message")]'
        self.header_xpath = '//div[contains(@class, "uix_message")]'
        self.date_xpath = 'div//span[@class="DateTime"]/@title'
        self.date_pattern = "%d %b %Y в %H:%M"
        self.author_xpath = 'div//span[@class="authorEnd"]/a/text()'
        self.title_xpath = '//div[@class="titleBar"]/h1/text()'
        self.post_text_xpath = 'div//div[@class="messageContent"]/article/blockquote'
        self.comment_block_xpath = 'div//div[@class="messageDetails"]/a/text()'
        self.avatar_xpath = 'div//a[@data-avatarhtml="true"]/img/@src'

        # main function
        self.main()

    def get_post_text(self, tag):
        post_text_block = tag.xpath(self.post_text_xpath)
        post_text = "\n".join([
            post_text.xpath('string()') for post_text in post_text_block
        ])

        return post_text.strip()
