# -- coding: utf-8 --
import re
import datetime
import dateparser

from .base_template import BaseTemplate


class AjanlarParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "ajanlar.org"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="posts"]/div[contains(@class, "post")]'
        self.header_xpath = '//div[@id="posts"]/div[contains(@class, "post")]'
        self.date_xpath = './/span[@class="post_date"]/text()'
        self.date_pattern = '%d.%m.%Y, %H:%M'
        self.author_xpath = './/div[@class="author_information"]//span[@class="largetext"]/a//text()'
        self.title_xpath = '//td[@class="thead"]/div/strong/text()'
        self.post_text_xpath = './/div[@class="post_body scaleimages"]/text()'
        self.comment_block_xpath = './/div[@class="post_head"]//a/text()'
        self.avatar_xpath = './/div[@class="author_avatar"]/a/img/@src'

        # main function
        self.main()

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = title[-1].strip() if title else None

        return title

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = date_block[0].replace('Saat:', '').strip() if date_block else None

        if not date:
            return ""

        # check if date is already a timestamp
        try:
            date = datetime.datetime.strptime(date, self.date_pattern).timestamp()
        except:
            try:
                date = float(date)
            except:
                err_msg = f"WARN: could not figure out date from: ({date}) using date pattern ({self.date_pattern})"
                print(err_msg)
                date = dateparser.parse(date).timestamp()
        if date:
            curr_epoch = datetime.datetime.today().timestamp()
            if date > curr_epoch:
                err_msg = f"ERROR: the timestamp ({date}) is after current time ({curr_epoch})"
                print(err_msg)
                raise RuntimeError(err_msg)
            return str(date)
        return ""