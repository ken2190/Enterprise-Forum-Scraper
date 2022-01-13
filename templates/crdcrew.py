import re

from .base_template import BaseTemplate


class CrdcrewParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "crdcrew.cc"
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.title_xpath = '//h1[@class="p-title-value"]//text()'
        self.comments_xpath = '//div[@class="message-inner"]'
        self.header_xpath = '//div[@class="message-inner"]'
        self.date_xpath = './/a/time/@data-time'
        self.post_text_xpath = './/div//div[@class="bbWrapper"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = './/div//div[@class="message-avatar-wrapper"]/a/img/@src'
        self.comment_block_xpath = './/div[@class="message-inner"]' \
                                   '//ul[contains(@class,"message-attribution-opposite--list")]/li[last()]/a/text()'
        self.author_xpath = './/div[contains(@class, "nadavoi")]//a[contains(@class, "username")]//text()|'\
            './/div[contains(@class, "message-userDetails")]//h4[contains(@class,"message-name")]//span/text()|'\
            './/div[contains(@class, "message-userDetails")]//h4[contains(@class,"message-name")]//text()'
        self.main()
