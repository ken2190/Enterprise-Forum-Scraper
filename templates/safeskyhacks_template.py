import re

from .base_template import BaseTemplate


class SafeskyhacksParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "safeskyhacks.com"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//li[contains(@class,"postcontainer")]'
        self.header_xpath = '//li[contains(@class,"postcontainer")]'
        self.date_xpath = './/span[@class="date"]//text()'
        self.author_xpath = './/a[contains(@class,"username")]//descendant::text()'
        self.title_xpath = '//span[contains(@class,"threadtitle")]//descendant::text()'
        self.post_text_xpath = './/div[contains(@class,"postbody")]//div[@class="content"]//descendant::text()[not(ancestor::div[@class="quote_container"])]'
        self.avatar_xpath = './/div[contains(@class,"userinfo")]//a[@class="postuseravatar"]//img/@src'
        self.comment_block_xpath =  './/div[contains(@class,"posthead")]//span[@class="nodecontrols"]/a//text()'

        # main function
        self.main()
