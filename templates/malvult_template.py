# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class MalvultParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "malvult.net"
        self.thread_name_pattern = re.compile(
            r'(.*)-\d+\.html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.mode = 'r'
        self.comments_xpath = '//ol[@class="messageList"]/li'
        self.header_xpath = '//ol[@class="messageList"]/li'
        self.date_xpath = './/span[@class="DateTime"]/@title'
        self.author_xpath = 'div//div[@class="uix_userTextInner"]/a[@class="username"]/text()'
        self.title_xpath = '//div[@class="titleBar"]/h1/text()'
        self.post_text_xpath = 'div//blockquote[contains(@class,"messageText")]/text()'
        self.comment_block_xpath = 'div//div[@class="messageDetails"]/a/text()'
        self.avatar_xpath = 'div//div[@class="uix_avatarHolderInner"]/a/img/@src'

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
                           self.pagination_pattern.search(x).group(1)))

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

    def get_post_text(self, tag):
        post_text = tag.xpath(self.post_text_xpath)

        post_text = "\n".join(
            [text.strip() for text in post_text if text.strip()]
        ) if post_text else ""

        if not post_text:
            post_text = tag.xpath(
                'div//blockquote[contains(@class,"messageText")]'
                '/span/div/text()'
            )
            post_text = "\n".join(
                [text.strip() for text in post_text if text.strip()]
            ) if post_text else ""

        return post_text.strip()
