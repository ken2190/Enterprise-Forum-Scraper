# -- coding: utf-8 --
import re
from .base_template import BaseTemplate


class RSTForumsParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "rstforums.com"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.title_xpath = '//span[@class="ipsType_break ipsContained"]/span/text()'
        self.comments_xpath = '//article[@id]'
        self.header_xpath = '//article[@id]'
        self.date_xpath = './/div//div[contains(@class,"ipsType_reset")]//time/@datetime'
        self.author_xpath = './/aside/h3/strong//text()'
        self.post_text_xpath = './/div//div[@data-role="commentContent"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = './/aside//li[@class="cAuthorPane_photo"]//a/img/@src'
        self.index = 1
        self.date_pattern = "%Y-%m-%dT%H:%M:%SZ"
        # main function
        self.main()
