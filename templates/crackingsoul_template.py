# -- coding: utf-8 --
import re
# import locale
import dateparser
import datetime

from .base_template import BaseTemplate


class CrackingSoulParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "crackingsoul.com"
        self.avatar_name_pattern = re.compile(r'avatar_(\d+\.\w+)')
        self.mode = 'r'
        self.comments_xpath = '//div[@id="posts"]/div[contains(@class,"post ")]'
        self.header_xpath = '//div[@id="posts"]/div[contains(@class,"post ")]'
        self.date_pattern = '%d-%m-%Y, %I:%M %p'
        self.date_xpath_1 = './/span[@class="post_date"]/text()'
        self.date_xpath_2 = './/span[@class="post_date"]/span[1]/@title'
        self.title_xpath = '//span[@class="active"]//text()'
        self.post_text_xpath = './/div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.comment_block_xpath = './/div[@class="post_head"]/div/strong/a/text()'
        self.avatar_xpath = './/div[@class="author_avatar"]/a/img/@src'
        self.author_xpath = './/div[contains(@class,"author_information")]//strong//text()'

        self.offset_hours = -2

        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath_1)
        date = date_block[0].strip() if date_block else None

        if not date:
            date_block = tag.xpath(self.date_xpath_2)
            date = date_block[0].strip() if date_block else None

        result = ""

        # check if date is already a timestamp
        try:
            date = datetime.datetime.strptime(date, self.date_pattern)
        except Exception as err1:
            print(f"WARN: could not figure out date from: ({date}) using date pattern ({self.date_pattern})")

            try:
                result = float(date)
            except:
                try:
                    date = dparser.parse(date, dayfirst=True)
                except:
                    try:
                        date = dateparser.parse(date)
                    except Exception as err2:
                        err_msg = f"ERROR: Parsing {date} date is failed. {err2}"
                        raise ValueError(err_msg)

        if isinstance(date, datetime.datetime):
            if self.offset_hours:
                date += datetime.timedelta(hours=self.offset_hours)
            result = str(date.timestamp())

        return result
