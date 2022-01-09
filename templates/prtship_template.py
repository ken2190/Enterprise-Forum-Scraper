# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class PrtShipParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "prtship.com"
        self.avatar_name_pattern = re.compile(r'.*\.(\d+)/')
        self.comments_xpath = '//div[@class="message-inner"]'
        self.header_xpath = '//div[@class="message-inner"]'
        self.date_xpath = 'div//a/time/@data-time'
        self.author_xpath = 'div//div[@class="message-userDetails"]/h4/a//text()'
        self.title_xpath = '//h1[@class="p-title-value"]/text()'
        self.post_text_xpath = 'div//article/div[@class="bbWrapper"]/text()|' \
                               'div//article/div[@class="bbWrapper"]/img[contains(@class,"smilie") and @alt]/@alt|' \
                               'div//article/div[@class="bbWrapper"]/'\
                               'descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'div//div[@class="message-avatar-wrapper"]/a'\
                            '[img/@src]/@href'
        self.avatar_ext = 'jpg'
        self.comment_block_xpath = 'div//header//a[contains(text(),"#")]/text()'

        # main function
        self.main()
