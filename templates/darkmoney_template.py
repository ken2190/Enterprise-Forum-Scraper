import datetime
import re

from .base_template import BaseTemplate


class DarkMoneyParser(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "darkmoney.at"
        self.thread_name_pattern = re.compile(
            r'(\d+)-\d+\.html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r".dateline=(\d+).")

        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.header_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.comment_block_xpath = 'table//td[2][@class="thead"]/a/strong//text()'
        self.post_text_xpath = 'table//tr[@valign="top"]/td[@class="alt1" and @id]/div[@id]/descendant::text()[not(ancestor::div[@style="margin:20px; margin-top:5px; "])]'

        self.date_xpath = 'table//td[1][@class="thead"]/a/following-sibling::text()'

        self.date_pattern = '%d-%m-%Y, %H:%M'
        self.title_xpath = 'table//tr[@valign="top"]/td[@class="alt1" and @id]/div[@class="smallfont"]/strong//text()'        
        self.avatar_xpath = './/td[1]//a[contains(@rel, "nofollow") and img]/img/@src'
        self.avatar_ext = 'jpg'
        self.mode = 'r+'
        self.date_pattern = '%d-%m-%Y, %H:%M'
        self.offset_hours = -3
        self.main()

    def get_author(self, tag):
        author = tag.xpath(
            'table//a[@class="bigusername"]//text()'
        )
        if not author:
            author = tag.xpath(
                'table//div[contains(@id, "postmenu_")]/text()'
            )
        if not author:
            author = tag.xpath(
                'table//a[@class="bigusername"]/span/b/text()'
            )
        if not author:
            author = tag.xpath(
                'table//a[@class="bigusername"]/font/strike/text()'
            )

        author = author[0].strip() if author else None

        return author

    @staticmethod
    def construct_date_string(date_block):
        date_string = date_block[0].strip() if date_block else None
        if 'Yesterday' in date_string:
            date = datetime.date.today() - datetime.timedelta(days=1)
            date_string = date_string.replace('Yesterday', date.strftime('%d-%m-%Y'))
        elif 'Today' in date_string:
            date = datetime.date.today()
            date_string = date_string.replace('Today', date.strftime('%d-%m-%Y'))
        return date_string

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date_string = self.construct_date_string(date_block)
        date = self.parse_date_string(date_string)
        return date
