# -- coding: utf-8 --
import re
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class WallStreetParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "wallstreet forum"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@class="main-content main-topic"]/*'
        self.header_xpath = '//div[@class="main-content main-topic"]/*'
        self.date_xpath = 'div//span[@class="post-link"]/a/text()'
        self.author_xpath = 'div//span[@class="post-byline"]/em/a/text()'
        self.title_xpath = '//h1[@class="main-title"]/a/text()'
        self.post_text_xpath = 'div//div[@class="entry-content"]/*[not(@class="quotebox")]/text()'
        self.comment_block_xpath = 'div//span[@class="post-num"]/text()'
        self.avatar_xpath = 'div//li[@class="useravatar"]/img/@src'

        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = ""
        if date_block:
            date = [d.strip() for d in date_block if d.strip()][0]

        try:
            pattern = "%Y-%m-%d %H:%M:%S"
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except:
            try:
                date = dparser.parse(date).timestamp()
                return str(date)
            except:
                pass

        return ""

    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if not author:
            author = tag.xpath(
                'tr//div[contains(@id, "postmenu_")]/text()'
            )

        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = title[-1].strip() if title else None

        return title
