# -- coding: utf-8 --
import re
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class TheCCParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "thecc.bz"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@class="post_wrapper"]'
        self.header_xpath = '//div[@class="post_wrapper"]'
        self.date_xpath = '//div[@class="smalltext"][strong]/text()'
        self.author_xpath = 'div[@class="poster"]/h4/a/text()'
        self.title_xpath = 'div//h5/a/text()'
        self.post_text_xpath = 'div//div[@class="post"]//div[@class="inner"]'
        self.avatar_xpath = 'div//img[@class="avatar"]/@src'
        self.comment_block_xpath = 'div[@class="postarea"]//div[@class="smalltext"]/strong/text()'

        # main function
        self.main()

    def extract_comments(self, html_response):
        comments = list()
        comment_blocks = html_response.xpath(self.comments_xpath)

        for index, comment_block in enumerate(comment_blocks[1:], 1):
            comment_id = self.get_comment_id(comment_block)
            if not comment_id:
                continue

            user = self.get_author(comment_block)
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            avatar = self.get_avatar(comment_block)
            pid = self.thread_id

            source = {
                'forum': self.parser_name,
                'pid': pid,
                'message': comment_text.strip(),
                'cid': str(index),
                'author': user,
            }
            if comment_date:
                source.update({
                    'date': comment_date
                })
            if avatar:
                source.update({
                    'img': avatar
                })
            comments.append({
                '_source': source,
            })

        return comments

    def get_date(self, tag):
        date = tag.xpath(self.date_xpath)
        if not date:
            return ""

        date_pattern = re.compile(r'(.*[aApP][mM])')
        match = date_pattern.findall(date[-1])
        date = match[0].strip() if match else ""
        if not date:
            return ""

        try:
            pattern = "%I:%M:%S %p"
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except:
            try:
                date = dparser.parse(date).timestamp()
                return str(date)
            except:
                pass

        return ""

    def get_post_text(self, tag):
        post_text_block = tag.xpath(self.post_text_xpath)
        post_text = "\n".join([
            post_text.xpath('string()') for post_text in post_text_block
        ])

        return post_text.strip()

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        if comment_block:
            comment_pattern = re.compile(r'Reply #(\d+) on:')
            match = comment_pattern.findall(comment_block[0])
            comment_id = match[0] if match else ""

        return comment_id.replace(',', '')
