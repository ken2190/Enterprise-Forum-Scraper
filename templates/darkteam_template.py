# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class DarkteamParser(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "darkteam.se"
        self.avatar_name_pattern = re.compile(r"/(\d+\.\w+)")
        self.comments_xpath = '//article[contains(@class,"message--post")]'
        self.header_xpath = '//article[contains(@class,"message--post")]'
        self.date_xpath = './/*[contains(@class,"message-attribution-main")]//time/@data-time|' \
                          './/ul[contains(@class,"message-attribution-main")]//time/@data-time'
        self.author_xpath = './/h4[contains(@class,"message-name")]//span/text()|' \
                            './/h4[contains(@class,"message-name")]//text()'
        self.post_text_xpath = './/div[contains(@class,"message-content")]//article/descendant::text()[not(ancestor::div[contains(@class,"bbCodeQuote")])]'
        self.title_xpath = '//div[contains(@class,"p-title")]/h1/text()'
        self.comment_block_xpath = './/div//header[@class="message-attribution"]/div/a/text()'
        self.avatar_xpath = './/a[contains(@class, "avatar")]//img/@src'

        # main function
        self.main()

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        if comment_block:
            comment_id = comment_block[-1].strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date_string = date_block[0].strip() if date_block else None
        date = self.parse_date_string(date_string)
        return date
