# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class XSSParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "xss.is"
        self.avatar_name_pattern = re.compile(r'.*\.(\d+)/')
        self.comments_xpath = '//div[@class="message-inner"]'
        self.header_xpath = '//div[@class="message-inner"]'
        self.date_xpath = 'div//div[@class="message-attribution-main"]/a/time/@data-time'
        self.author_xpath = 'div//div[@class="message-userDetails"]/h4/a/text()'
        self.title_xpath = '//h1[@class="p-title-value"]/text()'
        self.post_text_xpath = 'div//article/div[@class="bbWrapper"]/descendant::text()[not(ancestor::div[contains(@class, "bbCodeBlock--quote")])]'
        self.avatar_xpath = 'div//div[@class="message-avatar-wrapper"]/a/img/@src'
        self.comment_block_xpath = './/ul[@class="message-attribution-opposite message-attribution-opposite--list"]/li[last()]/a/text()'

        # main function
        self.main()

    def get_comment_id(self, tag):
        comment_id = ""
        if self.comment_block_xpath:
            comment_block = tag.xpath(self.comment_block_xpath)
            comment_block = ''.join(comment_block)
        else:
            return str(self.index)

        if comment_block:
            comment_id = ''.join(comment_block.split('#')[-1].split(' ')).strip()

        return comment_id.replace(',', '').replace('.', '')
