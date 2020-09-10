import re

from .base_template import BaseTemplate


class ox00secParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "0x00sec.org"
        self.avatar_name_pattern = re.compile(r'\d+/(\w+\.\w+)')
        self.index = 1
        self.mode = 'r'
        self.comments_xpath = '//div[@class="topic-body crawler-post"]|//article[contains(@id,"post_")]'
        self.header_xpath = '//div[@class="topic-body crawler-post"]|//article[contains(@id,"post_")]'
        self.date_xpath = './/time[@itemprop="datePublished"]/@datetime'
        self.author_xpath = './/span[@class="creator"]/a/descendant::text()'
        self.title_xpath = '//meta[@itemprop="headline"]/@content'
        self.post_text_xpath = './/div[@itemprop="articleBody"]/descendant::text()'
        self.avatar_xpath = './/div[contains(@class,"topic-avatar")]//img/@src'
        self.avatar_xpath = './/img[contains(@src,"avatar")]/@src'

        # main function
        self.main()
