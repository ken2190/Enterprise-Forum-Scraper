# -- coding: utf-8 --
import re
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class CannabisRoadParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "cannabis road"
        self.thread_name_pattern = re.compile(r'(index\.php.*topic=\d+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@class="post_wrapper"]'
        self.header_xpath = '//div[@class="post_wrapper"]'
        self.date_xpath = 'div//div[@class="smalltext"]/text()'
        self.date_pattern = '%B %d, %Y, %I:%M:%S  %p'
        self.author_xpath = 'div[@class="poster"]/h4//text()'
        self.title_xpath = 'div//h5/a/text()'
        self.post_text_xpath = 'div//div[@class="post"]//div[@class="inner"]/text()'

        # main function
        self.main()

    def get_pid(self):
        pid_pattern = re.compile(r'topic=(\d+)')
        pid = pid_pattern.findall(self.thread_id)
        pid = pid[0] if pid else self.thread_id

        return pid

    def get_date(self, tag):
        date = tag.xpath(self.date_xpath)
        date_pattern = re.compile(r'(.*[aApP][mM])')
        match = date_pattern.findall(date[-1])
        date = match[0].strip() if match else None
        try:
            date = datetime.datetime.strptime(date, self.date_pattern).timestamp()
            return str(date)
        except:
            try:
                date = dparser.parse(date).timestamp()
                return str(date)
            except:
                pass

        return ""

    def get_comment_id(self, tag):
        commentID = tag.xpath(
            'div[@class="postarea"]'
            '//div[@class="smalltext"]/strong/text()'
        )
        if commentID:
            comment_pattern = re.compile(r'Reply #(\d+) on:')
            match = comment_pattern.findall(commentID[0])
            commentID = match[0] if match else ""

        return commentID.replace(',', '')
