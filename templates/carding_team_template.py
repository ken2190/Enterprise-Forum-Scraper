# -- coding: utf-8 --
import re
# import locale
import datetime
import dateparser

from .base_template import BaseTemplate


class CardingTeamParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "cardingteam.cc"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//div[@class="newposts"]'
        self.header_xpath = '//div[@class="newposts"]'
        self.author_xpath = './/strong/span[@class="largetext"]/descendant::text()'
        self.title_xpath = '//td[@class="thead"]/div/strong/text()'
        self.post_text_xpath = './/div[contains(@class, "post_body")]/descendant::text()[not(ancestor::blockquote)]'
        self.comment_block_xpath = './/div[@class="float_right"]/strong/a/text()'
        self.avatar_xpath = './/div[@class="author_avatar"]/a/img/@src'

        # main function
        self.main()

    def get_date(self, tag):
        """
        Return empty value since this site has anonymous timestamp for every post.
        """
        return ''
