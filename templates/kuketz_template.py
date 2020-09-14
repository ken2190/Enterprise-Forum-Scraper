import re

from .base_template import BaseTemplate


class KuketzParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "forum.kuketz-blog.de"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//div[contains(@class,"post ")]'
        self.header_xpath = '//div[contains(@class,"post ")]'
        self.date_xpath = './/div[@class="postbody"]//time//text()'
        self.author_xpath = './/dl[contains(@class,"postprofile")]//a[contains(@class,"username")]/text()'
        self.post_text_xpath = './/div[@class="content"]//text()'
        self.avatar_xpath = './/img[@class="avatar"]/@src'
        self.title_xpath = '//h2[@class="topic-title"]//text()'
        self.author_xpath = './/dl[@class="postprofile"]//a[contains(@class,"username")]/text()|'\
                            './/dl[@class="postprofile"]//span[@class="username"]/text()'
        self.index = 1
        self.mode = 'r'

        # main function
        self.main()

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = title[0].strip().split(']')[-1] if title else None

        return title
