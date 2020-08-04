# -- coding: utf-8 --
import re
# import locale
import dateutil.parser as dparser

from .base_template import BaseTemplate


class CrackForumParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "crack-forum.ru"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[contains(@id, "posts")]/div[contains(@align,"center")]'
        self.header_xpath = '//div[contains(@id, "posts")]/div[contains(@align,"center")]'
        self.title_xpath = '//table[1]//tr/td[1]//tr[2]/td/strong/text()'
        self.post_text_xpath = './/div[contains(@id, "post_message")]/text()'
        self.comment_block_xpath = './/table//td[2][@class="thead"]//a//text()'
        self.date_xpath = './/table[contains(@class, "tborder")][1]//td[contains(@class, "thead")][1]/text()'
        self.mode = 'r'

        # main function
        self.main()

    def get_date(self, tag):
        date = ""
        date_block = tag.xpath(self.date_xpath)
        date_block = "".join(date_block)
        if date_block:
            date = date_block.strip()
        if not date:
            return ""

        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except:
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            './/table//a[contains(@class,"username")]//text()'
        )
        if not author:
            author = tag.xpath(
                './/table//div[contains(@id, "postmenu_")]/text()'
            )

        if not author:
            author = tag.xpath(
                './/table//a[@class="bigusername"]/span/b/text()'
            )

        if not author:
            author = tag.xpath(
                './/a[@class="bigusername"]/font/strike/text()'
            )

        author = ''.join(author)

        author = author.strip() if author else None
        return author

    def get_avatar(self, tag):
        avatar_block = tag.xpath(
            './/table[contains(@id, "post")]//tr[2]/td[1]//img/@src'
        )
        if not avatar_block:
            return ""

        if "image.php" in avatar_block[0]:
            avatar_name_pattern = re.compile(r'u=(\d+)')
            name_match = avatar_name_pattern.findall(avatar_block[0])
            if name_match:
                name = f'{name_match[0]}.jpg'
                return name

        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""

        return name_match[0]
