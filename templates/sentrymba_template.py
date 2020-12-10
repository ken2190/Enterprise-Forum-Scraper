# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class SentryMBAParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "sentry.mba"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="posts"]/div[@class="postbit"]/div[contains(@class,"standard")]'
        self.header_xpath = '//div[@id="posts"]/div[@class="postbit"]/div[contains(@class,"standard")]'
        self.date_xpath = 'div/div[@class="head"]/text()'
        self.date_pattern = '%m-%d-%Y, %I:%M %p'
        self.author_xpath = 'div/div[@class="style"]//strong/text()'
        self.title_xpath = '//div[@class="subject"]/text()'
        self.post_text_xpath = 'div[@class="content"]/div[@class="text scaleimages post_body scaleimages"]/text()'
        self.comment_block_xpath = 'div/div[@class="head"]/div[@class="right"]/a/text()'
        self.avatar_xpath = 'div//img[@class="avatarp radius100"]/@src'

        # main function
        self.main()

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(x) is not None,
                files
            )
        )
        sorted_files = sorted(
            filtered_files,
            key=lambda x: (self.thread_name_pattern.search(x).group(1),
                           x.split("-")[-1]))
        return sorted_files
        
    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if not author:
            author = tag.xpath(
                'div//div[@class="uix_userTextInner"]'
                '/a[@class="username"]/span/text()'
            )

        author = author[0].strip() if author else None
        return author
