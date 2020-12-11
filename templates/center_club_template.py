# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class CenterClubParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "center.club"
        self.avatar_name_pattern = re.compile(r".*m/\d+/(\d+\.\w+).*")
        self.comments_xpath = '//div[@class="message-inner"]'
        self.header_xpath = '//div[@class="message-inner"]'
        self.date_xpath = 'div//div[@class="message-attribution-main"]/a/time/@data-time'
        self.author_xpath = 'div//div[@class="message-userDetails"]/h4[@class="message-name"]/descendant::text()'
        self.title_xpath = '//h1[@class="p-title-value"]/text()'
        self.post_text_xpath = 'div//article/div[@class="bbWrapper"]/descendant::text()[not(ancestor::div[contains(@class, "bbCodeBlock bbCodeBlock--expandable bbCodeBlock--quote")])]'
        self.comment_block_xpath = 'div//ul[@class="message-attribution-opposite message-attribution-opposite--list"]/li/a/text()'
        self.avatar_xpath = './/div[@class="message-avatar-wrapper"]/a/img/@src'

        # main function
        self.main()
