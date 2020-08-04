# -- coding: utf-8 --
import re
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class VerifiedParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "verified (verified2ebdpvms.onion)"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//table[contains(@id, "post") and tr[@valign="top"]]'
        self.header_xpath = '//table[contains(@id, "post") and tr[@valign="top"]]'
        self.date_xpath = 'tr//td[@class="thead"]/text()'
        self.author_xpath = 'tr//div[contains(@id, "postmenu_")]/a/font/b/text()'
        self.title_xpath = '//span[@class="navbar"]/a/text()'
        self.post_text_xpath = 'tr//div[contains(@id, "post_message_")]/font/text()'
        self.comment_block_xpath = 'tr//a[contains(@id, "postcount")]/strong/text()'
        self.avatar_xpath = 'tr//div[@class="smallfont"]/a/img/@src'

        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = ""
        if date_block:
            date = [d.strip() for d in date_block if d.strip()][0]

        try:
            pattern = '%d.%m.%Y, %H:%M'
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
