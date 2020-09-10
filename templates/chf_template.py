import re
from .base_template import BaseTemplate


class ChfParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "chf.su"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//article[contains(@class,"message--post")]'
        self.header_xpath = '//article[contains(@class,"message--post")]'
        self.title_xpath = '//h1[@class="p-title-value"]//text()'
        self.date_xpath = './/time/@datetime'
        self.author_xpath = './/span[contains(@class,"username")]//text()'
        self.post_text_xpath = './/article[contains(@class,"selectToQuote")]/descendant::text()[not(ancestor::div[contains(@class,"bbCodeBlock--quote")])]'
        self.comment_block_xpath = './/ul[contains(@class,"message-attribution-opposite")]/li[last()]/a/text()'
        self.avatar_xpath = './/div[@class="message-avatar "]//img/@src'

        # main function
        self.main()
