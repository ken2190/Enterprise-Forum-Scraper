# -- coding: utf-8 --
import re
import utils

from .base_template import BaseTemplate


class BHFIOParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "bhf.io"
        self.avatar_name_pattern = re.compile(r'members/(\d+)/')
        self.comments_xpath = '//article[contains(@class,"message--post")]'
        self.header_xpath = '//article[contains(@class,"message--post")]'
        self.date_xpath = 'div//div[@class="message-attribution-main"]/a/time/@data-time'
        self.author_xpath = './/div[@class="message-userDetails"]/h4/descendant::text()'
        self.title_xpath = '//h1[@class="p-title-value"]/text()'
        self.comment_block_xpath = 'div//ul[@class="message-attribution-opposite message-attribution-opposite--list"]/li/a/text()'
        self.avatar_xpath = 'div//div[@class="message-avatar-wrapper"]/a[img/@src]/@href'
        self.post_text_xpath = 'div//article/div[@class="bbWrapper"]'\
                               '/descendant::text()[not(ancestor::div'\
                               '[contains(@class, "bbCodeBlock bbCodeBlock'\
                               '--expandable bbCodeBlock--quote")])]'
        self.avatar_ext = 'jpg'
        self.mode = 'r'

        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        return date_block[0]