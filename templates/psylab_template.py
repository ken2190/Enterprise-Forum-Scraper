# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class PsylabParser(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "psylab.cc"
        self.avatar_name_pattern = re.compile(r"/(\d+\.\w+)")
        self.comments_xpath = '//article[contains(@class,"message--post")]'
        self.header_xpath = '//article[contains(@class,"message--post")]'
        self.date_xpath = './/div[contains(@class,"message-attribution-main")]//time/@title|'\
            './/ul[contains(@class,"message-attribution-main")]//time/@title'
        self.author_xpath = './/h4[contains(@class,"message-name")]//span/text()|'\
            './/h4[contains(@class,"message-name")]//text()'
        self.post_text_xpath = './/div[contains(@class,"message-content")]//article/descendant::text()[not(ancestor::div[contains(@class,"bbCodeQuote")])]'
        self.title_xpath = '//div[contains(@class,"p-title")]/h1/text()'
        self.comment_block_xpath = './/ul[contains(@class,"message-attribution-opposite--list")]/li[2]/a/text()'
        self.avatar_xpath = './/a[contains(@class, "avatar")]//img/@src'

        # main function
        self.main()
