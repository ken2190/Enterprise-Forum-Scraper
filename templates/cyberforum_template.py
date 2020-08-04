# -- coding: utf-8 --
import re
# import locale
import dateutil.parser as dparser
from datetime import date, timedelta

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
        self.date_xpath = './/td[contains(@class,"alt2 smallfont")][1]//text()'
        self.author_xpath = './/span[contains(@class,"bigusername")]//text()'
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
        date_block = tag.xpath(self.date_xpath)[0]

        if not date:
            return ""

        Date = date_block.strip()

        try:
            Date = dparser.parse(Date).timestamp()
            return str(Date)
        except Exception:
            if not Date:
                return ''

            Date = Date.split(',')

            if ord(Date[0][-1]) == 1072:
                day = date.today() - timedelta(days=1)
            else:
                day = date.today()

            toparse = day.strftime("%B %d, %Y") + Date[-1]
            Date = dparser.parse(toparse).timestamp()

            return str(Date)

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
