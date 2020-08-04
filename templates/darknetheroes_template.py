# -- coding: utf-8 --
import re
import traceback
import utils
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class DarkNetHeroesParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = kwargs.get('parser_name')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.thread_name_pattern = re.compile(r'index\.php.*topic=\d+')
        self.comments_xpath = '//div[@class="post_wrapper"]'
        self.header_xpath = '//div[@class="post_wrapper"]'
        self.author_xpath = 'div[@class="poster"]/h4/a/text()'
        self.title_xpath = 'div//h5/a/text()'
        self.post_text_xpath = 'div//div[@class="post"]//div[@class="inner"]/text()'

        # main function
        self.main()

    def get_pid(self):
        pid_pattern = re.compile(r'topic=(\d+)')
        pid = pid_pattern.findall(self.thread_id)
        pid = pid[0] if pid else self.thread_id

        return pid

    def get_filtered_files(self, files):
        final_files = list()
        for file in files:
            file_name_only = file.split('/')[-1]
            if file_name_only.startswith('index.php') and\
               'action=' not in file_name_only and\
               'board=' not in file_name_only:
                final_files.append(file)

        return sorted(final_files)

    def get_date(self, tag):
        date = tag.xpath(
            'div//div[@class="smalltext"]/text()'
        )
        date_pattern = re.compile(r'(.*)\s+')
        match = date_pattern.findall(date[-1])
        date = match[0].strip() if match else None
        try:
            pattern = '%B %d, %Y, %H:%M'
            date = datetime.datetime.strptime(date, pattern).timestamp()
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

    def get_avatar(self, tag):
        pass
