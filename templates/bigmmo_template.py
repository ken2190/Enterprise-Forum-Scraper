# -- coding: utf-8 --
import datetime
import re
# import locale
import dateparser

from .base_template import BaseTemplate


class BigMMOParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "bigmmo.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//ol[@class="messageList"]/li[contains(@class,"message")]'
        self.header_xpath = '//ol[@class="messageList"]/li[contains(@class,"message")]'
        self.date_pattern = "%d/%m/%y lúc %H:%M"
        self.date_xpath = './/div[@class="messageDetails"]//abbr[@class="DateTime"]/@data-time|' \
                          './/div[contains(@class,"messageDetails")]//span[contains(@class,"DateTime")]/@title|' \
                          './/div[contains(@class,"messageDetails")]//span[contains(@class,"DateTime")]/text()|' \
                          './/div[@class="messageDetails"]//abbr[@class="DateTime"]/@data-datestring|' \
                          './/div[@class="privateControls"]//abbr[@class="DateTime"]/@data-time|' \
                          './/div[@class="privateControls"]//span[@class="DateTime"]/@title|' \
                          './/div[@class="privateControls"]//abbr[@class="DateTime"]/@data-datestring'

        self.post_text_xpath = './/div[contains(@class,"messageContent")]//article/blockquote' \
                               '/descendant::text()[not(ancestor::div[contains(@class,"bbCodeQuote")])]'
        self.title_xpath = '//div[contains(@class,"media__body")]/h1//text()|' \
                           '//div[contains(@class,"titleBar")]/h1//text()'
        self.comment_block_xpath = './/div[@class="messageDetails"]/a//text()'
        self.author_xpath = './/div[contains(@class,"messageUserBlock")]//a[contains(@class,"username")]//text()'

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

    def get_avatar(self, tag):
        avatar_block = tag.xpath(
            './/div[contains(@class,"avatarHolder")]//img/@src'
        )
        if not avatar_block:
            return ""

        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""

        if name_match[0].startswith('svg'):
            return ''

        return name_match[0]

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date_block = date_block[0]
        date = date_block.strip() if date_block else ""
        try:
            date = float(date)
            return str(date)
        except:
            try:
                date = datetime.datetime.strptime(date, self.date_pattern).timestamp()
            except:
                print(f"WARN: could not figure out date from: ({date}) using date pattern ({self.date_pattern})")
                date = dateparser.parse(date).timestamp()
            return str(date)

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)[0]
        title = title.strip().split(']')[-1] if title else None
        return title

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)

        if comment_block:
            comment_id = comment_block[-1].strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')
