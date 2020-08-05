# -- coding: utf-8 --
import re
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class TheHubParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "thehub.net"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'attach=(\d+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@class="post_wrapper"]'
        self.header_xpath = '//div[@class="post_wrapper"]'
        self.date_xpath = 'div//div[@class="smalltext"]/text()'
        self.author_xpath = 'div/h4/a/text()'
        self.title_xpath = 'div//h5/a/text()'
        self.post_text_xpath = 'div//div[@class="post"]//div[@class="inner"]/descendant::text()[not(ancestor::blockquote) and not(div[@class="quoteheader"]) and not(div[@class="quotefooter"])]'
        self.avatar_xpath = 'div//li[@class="avatar"]/a/img/@src'
        self.avatar_ext = 'jpg'
        self.comment_block_xpath = 'div[@class="postarea"]//div[@class="smalltext"]/strong/text()'

        # main function
        self.main()

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(
                    x.split('/')[-1]) is not None,
                files
            )
        )
        sorted_files = sorted(
            filtered_files,
            key=lambda x: int(self.thread_name_pattern.search(
                x.split('/')[-1]).group(1)))

        return sorted_files

    def get_date(self, tag):
        date = tag.xpath(self.date_xpath)
        date_pattern = re.compile(r'(.*[aApP][mM])')
        match = date_pattern.findall(date[-1])
        date = match[0].strip() if match else None

        try:
            pattern = '%B %d, %Y, %I:%M:%S  %p'
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
        commentID = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        if comment_block:
            comment_pattern = re.compile(r'Reply #(\d+) on:')
            match = comment_pattern.findall(comment_block[0])
            commentID = match[0] if match else ""

        return commentID.replace(',', '')
