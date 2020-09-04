# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class RuntimeParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "runtime.rip"
        self.avatar_name_pattern = re.compile(r".*avatar_(\d+\.\w+)")
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//article[contains(@class,"post-article")]'
        self.header_xpath = '//article[contains(@class,"post-article")]'
        self.date_xpath = 'div//span[contains(@class, "post_date")]/text()'
        self.author_xpath = './/div[contains(@class,"post-username")]/a/span/text()'
        self.title_xpath = '//div[@class="thread-header"]/h1/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = 'div//div[@class="right postbit-number"]/strong/a/text()'

        # main function
        self.main()


    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if author:
            author = author[0].strip()
            return author
        else:
            return ''