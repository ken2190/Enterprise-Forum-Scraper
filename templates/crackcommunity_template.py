# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class CrackCommunityParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "crackcommunity.com"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//ol[@class="messageList"]/li[contains(@class,"message")]'
        self.header_xpath = '//ol[@class="messageList"]/li[contains(@class,"message")]'
        self.date_xpath = './/div[contains(@class,"messageMeta")]//span[contains(@class,"DateTime")]/text()'
        self.author_xpath = './/div[contains(@class,"messageMeta")]//span[contains(@class,"authorEnd")]/a/text()'
        self.post_text_xpath = './/div[contains(@class,"messageContent")]//article/blockquote/descendant::text()[not(ancestor::div[contains(@class,"bbCodeQuote")])]'
        self.title_xpath = '//div[contains(@class,"titleBar")]/h1/text()'
        self.comment_block_xpath = './/div[@class="publicControls"]/a//text()'
        self.avatar_xpath= './/div[contains(@class,"avatarHolder")]//img/@src'

        # main function
        self.main()
