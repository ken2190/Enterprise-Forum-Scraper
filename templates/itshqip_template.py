import re

from .base_template import BaseTemplate


class ItshqipParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "forum.itshqip.com"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.mode = 'r'
        self.comments_xpath = '//ol[@class="messageList"]/li[contains(@class,"message")]'
        self.header_xpath = '//ol[@class="messageList"]/li[contains(@class,"message")]'
        self.date_xpath = './/div[contains(@class,"messageMeta")]//abbr[contains(@class,"DateTime")]/@data-time|' \
                          './/div[contains(@class,"messageMeta")]//span[contains(@class,"DateTime")]/@title'
        self.author_xpath = './/div[contains(@class,"messageMeta")]//span[contains(@class,"authorEnd")]/a/text()'
        self.post_text_xpath = './/div[contains(@class,"messageContent")]//article/blockquote/descendant::text()[not(ancestor::div[contains(@class,"bbCodeQuote")])]'
        self.avatar_xpath = './/div[contains(@class,"avatarHolder")]//img/@src'
        self.title_xpath = '//div[contains(@class,"titleBar")]/h1/text()'
        self.comment_block_xpath = './/div[@class="publicControls"]/a//text()'
        self.date_pattern = '%b %d, %Y at %I:%M %p'
        self.offset_hours = -1  # DST
        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date_string = date_block[0].strip() if date_block else None
        date = self.parse_date_string(date_string)
        return date