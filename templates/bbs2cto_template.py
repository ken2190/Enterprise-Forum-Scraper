import re

from .base_template import BaseTemplate


class Bbs2ctoParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "bbs.2cto.com"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//div[@class="read_t"]'
        self.header_xpath = '//div[@class="read_t"]'
        self.title_xpath = '//h1[@id="subject_tpc"]//text()[1]'
        self.author_xpath = './/div[contains(@class,"readName")]/a//text()'
        self.post_text_xpath = './/div[contains(@class,"tpc_content")]//text()'
        self.avatar_xpath = './/a[contains(@class,"userCard")]/img/@src'
        self.comment_block_xpath = './/div[contains(@class,"tipTop")]/a//text()'
        self.date_xpath = './/div[contains(@class,"tipTop")]/span[2]//text()'
        self.mode = 'r'

        # main function
        self.main()
