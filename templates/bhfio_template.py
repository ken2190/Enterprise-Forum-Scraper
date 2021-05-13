# -- coding: utf-8 --
import re
import utils
import datetime
import dateparser

from .base_template import BaseTemplate


class BHFIOParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "bhf.io"
        self.avatar_name_pattern = re.compile(r'members/(\d+)/')
        self.comments_xpath = '//article[contains(@class,"message--post")]'
        self.header_xpath = '//article[contains(@class,"message--post")]'
        self.date_xpath = './/div[contains(@class,"message-attribution-main")]//time/@title|' \
                          './/ul[contains(@class,"message-attribution-main")]//time/@title'
        self.author_xpath = './/div[@class="message-userDetails"]/h4/descendant::text()'
        self.title_xpath = '//h1[@class="p-title-value"]/text()'
        self.comment_block_xpath = './/ul[contains(@class,"message-attribution-opposite--list")]/li[last()]/a/text()'
        self.avatar_xpath = 'div//div[@class="message-avatar-wrapper"]/a[img/@src]/@href'
        self.post_text_xpath = 'div//article/div[@class="bbWrapper"]' \
                               '/descendant::text()[not(ancestor::div' \
                               '[contains(@class, "bbCodeBlock bbCodeBlock' \
                               '--expandable bbCodeBlock--quote")])]'
        self.avatar_ext = 'jpg'
        self.mode = 'r'

        self.offset_hours = 5

        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = date_block[0].strip() if date_block else None

        if not date:
            return ''

        # check if date is already a timestamp
        try:
            date = float(date)
        except:
            try:
                date = dateparser.parse(date)

                if self.offset_hours:
                    date += datetime.timedelta(hours=self.offset_hours)
                date = date.timestamp()
            except Exception as err:
                err_msg = f"ERROR: Parsing {date} date is failed. {err}"
                raise ValueError(err_msg)

        curr_epoch = datetime.datetime.today().timestamp()

        if date > curr_epoch:
            err_msg = f"ERROR: the timestamp ({date}) is after current time ({curr_epoch})"
            print(err_msg)
            raise RuntimeError(err_msg)
        return str(date)
