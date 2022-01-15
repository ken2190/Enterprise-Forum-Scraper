import re

from datetime import datetime
from .base_template import BaseTemplate


class ImhatimiParser(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "imhatimi.org"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//article[contains(@class,"message--post")]'
        self.header_xpath = '//article[contains(@class,"message--post")]'
        self.author_xpath = './/div[@class="message-userDetails"]/h4/a//text()'
        self.post_text_xpath = './/article[contains(@class,"selectToQuote")]' \
                               '/descendant::text()[not(ancestor::blockquote)]'
        self.title_xpath = '//h1[@class="p-title-value"]/text()'
        self.comment_block_xpath = './/ul[contains(@class,"message-attribution-opposite--list")]/li[last()]/a/text()'
        self.avatar_xpath = './/div[@class="message-avatar "]//img/@src'
        self.date_xpath = './/ul[contains(@class, "message-attribution-main")]' \
                          '//time[contains(@class, "u-dt")]/@datetime'
        self.date_pattern = '%Y-%m-%dT%H:%M:%S'

        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)

        if date_block:
            date_blocks = ' '.join(date_block)
            date = date_blocks.strip()
        else:
            return None

        try:
            date = datetime.strptime(
                date.strip()[:-5],
                self.date_pattern
            ).timestamp()
            return str(date)
        except Exception:
            return ""

        return ""
