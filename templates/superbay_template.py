# -- coding: utf-8 --
import datetime
import re

import dateparser

from .base_template import BaseTemplate


class SuperBayParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "superbay_suprbayoubiexnmp"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[contains(@class,"post classic")]'
        self.header_xpath = '//div[contains(@class,"post classic")]'
        self.date_xpath = './/span[@class="post_date"]/span[1]/@title|.//span[@class="post_date"]/text()'
        self.author_xpath = './/div[@class="author_information"]//span[@class="largetext"]/descendant::text()'
        self.title_xpath = '//td[@class="thead"]/div/strong/text()'
        self.post_text_xpath = './/div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = './/div[@class="author_avatar"]//img/@src'
        self.avatar_ext = 'jpg'
        self.comment_block_xpath = './/div[@class="post_head"]//strong/a/text()'
        self.date_pattern = "%b %d, %Y, %H:%M %p"
        self.offset_hours = 4
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

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)

        if comment_block:
            comment_id = comment_block[-1].strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')

    def construct_date_string(self, date_block):
        if not date_block:  # if xpaths don't match return empty string.
            return None
        if ':' in date_block[0]:  # if title has complete date with time. return it as is.
            return date_block[0].strip()
        else:  # if title does not have time in it, grabs it from span text and append it.
            return ''.join(date_block).strip()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = self.construct_date_string(date_block)

        if not date:
            return ""

        # check if date is already a timestamp
        try:
            date_obj = datetime.datetime.strptime(date, self.date_pattern)
            if self.offset_hours:
                date_obj += datetime.timedelta(hours=self.offset_hours)
            date = date_obj.timestamp()
        except:
            try:
                date = float(date)
            except:
                err_msg = f"WARN: could not figure out date from: ({date}) using date pattern ({self.date_pattern})"
                print(err_msg)
                date_obj = dateparser.parse(date)
                if self.offset_hours:
                    date_obj += datetime.timedelta(hours=self.offset_hours)
                date = date_obj.timestamp()

        if date:
            curr_epoch = datetime.datetime.today().timestamp()
            if date > curr_epoch:
                err_msg = f"ERROR: the timestamp ({date}) is after current time ({curr_epoch})"
                print(err_msg)
                raise RuntimeError(err_msg)
            return str(date)
        return ""
