#  coding: utf8
import re
from .base_template import BaseTemplate


class XrpChatParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "xrpchat.com"
        self.mode = 'r'
        self.avatar_name_pattern = re.compile(r'(\w+.\w+)$')
        self.comments_xpath = '//article[contains(@id, "elComment_")]'
        self.header_xpath = '//article[contains(@id, "elComment_")]'
        self.date_xpath = 'div//div[@class="ipsType_reset"]//time/@title'
        self.author_xpath = './/h3[contains(@class,"cAuthorPane_author")]/a//'\
                            'text()'
        self.title_xpath = '//span[@class="ipsType_break ipsContained"]'\
                           '/span/text()'
        self.post_text_xpath = './/div[contains(@class,"cPost_content")]/'\
                               'descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'aside//li[@class="cAuthorPane_photo"]/a/img/@src'
        self.index = 1

        # main function
        self.main()
