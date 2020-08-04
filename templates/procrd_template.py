# -- coding: utf-8 --
import re
import locale

from .base_template import BaseTemplate


class ProcrdParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        super().__init__(*args, **kwargs)
        self.parser_name = "procrd.me"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//ol[@class="messageList"]/li'
        self.header_xpath = '//ol[@class="messageList"]/li'
        self.date_xpath = 'div//a[@class="datePermalink"]/span/@title'
        self.date_pattern = "%d %b %Y в %H:%M"
        self.author_xpath = 'div//h3[@class="userText"]/a[@class="username"]/text()'
        self.title_xpath = '//div[@class="titleBar"]/h1/text()'
        self.post_text_xpath = 'div//blockquote[contains(@class,"messageText")]/descendant::text()[not(ancestor::div[@class="bbCodeBlock bbCodeQuote"])]'
        self.avatar_xpath = 'div//div[@class="avatarHolder"]/a/img/@src'
        self.comment_block_xpath = 'div//div[@class="publicControls"]/a/text()'

        # main function
        self.main()

    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if not author:
            author = tag.xpath(
                'div//h3[@class="userText"]'
                '/a[@class="username"]/span/text()'
            )

        author = author[0].strip() if author else None
        return author
