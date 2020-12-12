import re

from .base_template import BaseTemplate


class AltenensParser(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "altenens.org"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//article[contains(@class,"message--post")]'
        self.author_xpath = './/div[@class="message-userDetails"]/h4/a//text()'
        self.post_text_xpath = './/article[contains(@class,"selectToQuote")]/descendant::text()[not(ancestor::blockquote)]'
        self.title_xpath = '//h1[@class="p-title-value"]//text()'
        self.comment_block_xpath = './/ul[contains(@class,"message-attribution-opposite")]/li/a//text()'
        self.header_xpath = '//article[contains(@class,"message--post")]'
        self.avatar_xpath = './/div[@class="message-avatar "]//img/@src'
        self.date_xpath = './/time//text()'

        # main function
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
