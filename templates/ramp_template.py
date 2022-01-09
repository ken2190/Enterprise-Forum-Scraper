import re

from .base_template import BaseTemplate


class RampParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "ramp"
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.title_xpath = '//h1[@class="p-title-value"]//text()'
        self.comments_xpath = '//article[contains(@class,"message--post")]'
        self.header_xpath = '//article[contains(@class,"message--post")]'
        self.author_xpath = 'div[@class="message-userDetails"]/h4/a//text()'
        self.post_text_xpath = './/div//div[@class="bbWrapper"]/descendant::text()[not(ancestor::blockquote)]'
        self.comment_block_xpath = './/ul[contains(@class,"message-attribution-opposite")]/li/a//text()'
        self.avatar_xpath = './/div//div[@class="message-avatar-wrapper"]/a/img/@src'
        self.date_xpath = './/a/time/@data-time'
        self.main()

    def get_author(self, tag):
        author = tag.xpath(
            'div//div[@class="message-userDetails"]/h4/a/text()'
        )
        if not author:
            author = tag.xpath(
                'div//div[@class="message-userDetails"]/h4/a/span/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="message-userDetails"]/h4/span/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="message-userDetails"]/h4/span/a/text()'
            )

        author = author[0].strip() if author else None
        return author

