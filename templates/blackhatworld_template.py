# -- coding: utf-8 --
import re
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class BlackHatWorldParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "blackhatworld.com"
        self.avatar_name_pattern = re.compile(r".*/(\w+\.\w+)")
        self.comments_xpath = '//article[contains(@class,"message--post")]'
        self.header_xpath = '//article[contains(@class,"message--post")]'
        self.date_xpath = 'div//div[@class="message-attribution-main"]/a/time/@data-time'
        self.author_xpath = './/div[@class="message-userDetails"]/h4/a/descendant::text()'
        self.title_xpath = '//h1[@class="p-title-value"]/text()'
        self.comment_block_xpath = './/ul[@class="message-attribution-opposite message-attribution-opposite--list"]/li[2]/a/text()'
        self.avatar_xpath = './/div[@class="message-avatar-wrapper"]/a/img/@src'
        self.post_text_xpath = 'div//article/div[@class="bbWrapper"]'\
                               '/descendant::text()[not(ancestor::blockquote)]'
        self.mode = 'r'

        # main function
        self.main()
