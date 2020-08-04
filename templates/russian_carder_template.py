# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class RussianCarderParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "russiancarders.se"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@class="message-inner"]'
        self.header_xpath = '//div[@class="message-inner"]'
        self.date_xpath = 'div//header[@class="message-attribution"]/a/time/@title'
        self.date_pattern = "%b %d, %Y at %I:%M %p"
        self.author_xpath = 'div//div[@class="message-userDetails"]/h4/a/text()'
        self.title_xpath = '//h1[@class="p-title-value"]/text()'
        self.post_text_xpath = 'div//article/div[@class="bbWrapper"]/descendant::text()[not(ancestor::div[contains(@class, "bbCodeBlock bbCodeBlock--expandable bbCodeBlock--quote")])]'
        self.avatar_xpath = 'div//div[@class="message-avatar-wrapper"]/a/img/@src'
        self.comment_block_xpath = 'div//header[@class="message-attribution"]/div/a/text()'

        # main function
        self.main()
