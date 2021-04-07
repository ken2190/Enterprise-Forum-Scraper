# -- coding: utf-8 --
import re
# import locale
import dateutil.parser as dparser
import dateparser
from datetime import date, timedelta
import datetime

from .base_template import BaseTemplate

class CyberForumParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "cyberforum.ru"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.mode = 'r'
        self.comments_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.header_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.date_pattern = '%d.%m.%Y, %H:%M'
        self.date_xpath_1 = './/td[contains(@class,"alt2 smallfont")][1]//text()'
        self.date_xpath_2 = './/div[contains(@class,"smallfont shade")]/text()'
        self.author_xpath = './/*[contains(@class,"bigusername")]//text()'
        self.title_xpath = '//h1/text()'
        self.post_text_xpath = './/div[contains(@id, "post_message")]//text()[not(ancestor::div[@class="quote_container"])]'
        self.comment_block_xpath = './/td[contains(@class,"alt2 smallfont")][2]//b/text()'

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
        date_block = tag.xpath(self.date_xpath_1)
        date = date_block[0].strip() if date_block else None

        if not date:
            date_block = tag.xpath(self.date_xpath_2)
            date = date_block[0].strip() if date_block else None

        # check if date is already a timestamp
        try:
            date = datetime.datetime.strptime(date, self.date_pattern).timestamp()
            return str(date)
        except:
            try:
                date = float(date)
                return date
            except:
                try:
                    date = dateparser.parse(date).timestamp()
                    return str(date)
                except:
                    pass

        return ""

    def get_avatar(self, tag):
        avatar_block = tag.xpath(
            'table//a[contains(@href, "member.php")]/img/@src'
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
