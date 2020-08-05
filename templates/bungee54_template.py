# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class Bungee54Parser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "bungee 54"
        self.thread_name_pattern = re.compile(r'viewtopic\.php.*id=(\d+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@class="main-content main-topic"]/div'
        self.header_xpath = '//div[@class="main-content main-topic"]/div'
        self.date_xpath = 'div//span[@class="post-link"]/a/text()'
        self.date_pattern = "%Y-%m-%d %H:%M:%S"
        self.title_xpath = '//h1[@class="main-title"]/a/text()'
        self.post_text_xpath = 'div//div[@class="entry-content"]/*/text()'
        self.comment_block_xpath = 'div//span[@class="post-num"]/text()'

        # main function
        self.main()

    def get_pid(self):
        pid_pattern = re.compile(r'id=(\d+)')
        pid = pid_pattern.findall(self.thread_id)
        pid = pid[0] if pid else self.thread_id

        return pid

    def get_author(self, tag):
        author = tag.xpath(
            'div//span[@class="post-byline"]/strong/text()'
        )
        if not author:
            author = tag.xpath(
                'div//span[@class="post-byline"]/em/a/text()'
            )

        author = author[0].strip() if author else None
        return author
