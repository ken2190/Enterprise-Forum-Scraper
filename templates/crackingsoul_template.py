# -- coding: utf-8 --
import re
#import locale
import dateutil.parser as dparser

from .base_template import BaseTemplate

class CrackingSoulParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "crackingsoul.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.mode = 'r'
        self.comments_xpath = '//div[@id="posts"]/div[contains(@class,"post ")]'
        self.header_xpath = '//div[@id="posts"]/div[contains(@class,"post ")]'
        self.date_xpath = './/span[@class="post_date"]/text()'
        self.title_xpath = '//span[@class="active"]//text()'
        self.post_text_xpath = './/div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.comment_block_xpath = './/div[@class="post_head"]/div/strong/a/text()'
        self.avatar_xpath = './/div[@class="author_avatar"]/a/img/@src'

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

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date_block = ''.join(date_block)
        date = date_block.strip() if date_block else ""

        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except:
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            './/div[contains(@class,"author_information")]//strong//text()'
        )
        if not author:
            author = tag.xpath(
                './/div[contains(@class,"post_author")]/a/span//text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]/strong//b/span/text()'
            )

        author = ''.join(author)
        author = author.strip() if author else None

        return author

    def get_post_text(self, tag):
        post_text_block = tag.xpath(self.post_text_xpath)
        post_text = "".join([
            post_text.strip() for post_text in post_text_block
        ])
        return post_text[2:].strip()
