import re
from .base_template import BaseTemplate


class ChknetParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "forum.chknet.cc"
        self.avatar_name_pattern = re.compile(r'avatar=(\S+\.\w+)')
        self.comments_xpath = '//div[contains(@class,"post ")]'
        self.header_xpath = '//div[contains(@class,"post ")]'
        self.date_xpath = './/p[@class="author"]/text()[3]'
        self.post_text_xpath = './/div[@class="content"]//text()'
        self.title_xpath = '//h2[@class="topic-title"]//text()'
        self.avatar_xpath = './/img[@class="avatar"]/@src'
        self.author_xpath = './/dl[contains(@class,"postprofile")]//'\
                            'a[contains(@class,"username")]/text()'
        self.index = 1
        self.mode = 'r'

        # main function
        self.main()
