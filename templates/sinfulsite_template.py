# -- coding: utf-8 --
import datetime
import re

import dateparser

from .base_template import BaseTemplate


class SinfulSiteParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "sinfulsite.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[contains(@class,"anchor post")]'
        self.header_xpath = '//div[contains(@class,"anchor post")]'
        self.date_xpath = './/div[@class="time fullwidth"]//text()[1]'
        self.date_title_xpath = './/div[@class="time fullwidth"]/span[1]/@title'
        self.date_extract_regex = r'(19|20)\d\d-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01]), (\d{2}):(\d{2}):(\d{2})'
        self.author_xpath = './/div[contains(@class,"authorbit")]/div[3]//text()'
        self.title_xpath = '//div[@class="marginmid"][1]/text()'
        self.post_text_xpath = './/div[contains(@class,"textcontent") or contains(@class,"post_body")]//descendant::text()[not(ancestor::div[@class="hidelock"])]'
        self.avatar_xpath = './/div[@class="author_avatar"]//img/@src'
        self.comment_block_xpath = './/div[@class="time fullwidth"]/div[1]/a/text()'
        self.date_pattern = '%Y-%m-%d, %H:%M:%S'
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

    def parse_date(self, date_str):
        date = ""
        try:
            date = datetime.datetime.strptime(date_str, self.date_pattern).timestamp()
        except:
            try:
                date = float(date_str)
            except:
                err_msg = f"WARN: could not figure out date from: ({date_str}) using date pattern ({self.date_pattern})"
                print(err_msg)
                date = dateparser.parse(date_str).timestamp()
        return date

    def extract_date(self, date_str):
        m = re.match(self.date_extract_regex, date_str)
        if m:
            return m[0]
        return None

    def extract_str(self, string, regex_pattern):
        m = re.match(regex_pattern, string)
        if m:
            return m[0]
        return None

    def get_date(self, tag):
        date_title = tag.xpath(self.date_title_xpath)
        if date_title and self.extract_str(date_title[0], self.date_extract_regex):
            date = date_title[0].strip()
        else:
            date_block = tag.xpath(self.date_xpath)
            date = ''.join([date_val for date_val in date_block if date_val and '#' not in date_val]).strip()
        if not date:
            return ""

        if 'Yesterday' in date or 'Today' in date:
            time_str = date.split(',')[-1].strip()
            date = f"{date_title[0]}, {time_str}"
        extracted_date = self.extract_str(date, self.date_extract_regex)
        if extracted_date:
            date = extracted_date

        date = self.parse_date(date)
        if date:
            curr_epoch = datetime.datetime.now().timestamp()
            if date > curr_epoch:
                err_msg = f"ERROR: the timestamp ({date}) is after current time ({curr_epoch})"
                print(err_msg)
                raise RuntimeError(err_msg)
            return str(date)
        return ""
