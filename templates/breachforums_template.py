# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class BreachForumsParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "breachforums.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="posts"]/div[contains(@class, "post")]'
        self.header_xpath = '//div[@id="posts"]/div[contains(@class, "post")]'
        self.date_xpath = 'div//span[@class="post_date"]/text()'
        self.date_pattern = '%m-%d-%Y, %I:%M %p'
        self.author_xpath = 'div//div[@class="author_information"]//span[@class="largetext"]/a/span//text()'
        self.title_xpath = '//span[@class="crumbs"]/span/a/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]/text()'
        self.comment_block_xpath = 'div//div[@class="post_head"]//a/text()'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'

        # main function
        self.main()
