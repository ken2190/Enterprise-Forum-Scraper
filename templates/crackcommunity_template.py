# -- coding: utf-8 --
import re
from .base_template import BaseTemplate

class CrackCommunityParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "crackcommunity.com"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//li[contains(@id,"post-") and contains(@class, "message")]'
        self.header_xpath = '//li[contains(@id,"post-") and contains(@class, "message")]'
        self.date_xpath = './/a[@class="datePermalink"]//abbr/@data-time|' \
                          './/a[@class="datePermalink"]//span/@title'
        self.post_text_xpath = './/div[contains(@class,"messageContent")]//article/blockquote/descendant::text()[not(ancestor::div[contains(@class,"bbCodeQuote")])]'
        self.title_xpath = '//div[contains(@class,"titleBar")]/h1/text()'
        self.comment_block_xpath = './/div[@class="publicControls"]/a//text()'
        self.avatar_xpath= './/div[contains(@class,"avatarHolder")]//img/@src'
        self.date_pattern = "%b %d, %Y at %I:%M %p"
        self.offset_hours = -1

        # main function
        self.main()

    def get_author(self, tag):
        author = tag.attrib["data-author"]
        if author:
            author = author.strip()
            return author
        else:
            return ''

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date_string = date_block[0].strip() if date_block else None
        date = self.parse_date_string(date_string)
        return date
