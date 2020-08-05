# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class CarderhubParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "carderhub.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'(\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@class="message-inner"]'
        self.header_xpath = '//div[@class="message-inner"]'
        self.date_xpath = 'div//div[@class="message-attribution-main"]/a/time/@data-time'
        self.author_xpath = 'div//div[@class="message-userDetails"]/h4/a//text()'
        self.title_xpath = '//h1[@class="p-title-value"]/text()'
        self.post_text_xpath = 'div//article/div[@class="bbWrapper"]/descendant::text()[not(ancestor::div[contains(@class, "bbCodeBlock bbCodeBlock--expandable bbCodeBlock--quote")])]'
        self.comment_block_xpath = 'div//ul[@class="message-attribution-opposite message-attribution-opposite--list"]/li/a/text()'
        self.avatar_xpath = 'div//div[@class="message-avatar-wrapper"]/a/img/@alt'
        self.avatar_ext = 'jpg'

        # main function
        self.main()

    def get_date(self, tag):
        date = tag.xpath(self.date_xpath)
        return date[0] if date else ''
