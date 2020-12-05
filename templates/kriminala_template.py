# -- coding: utf-8 --
import os
import utils
import locale
import re
import dateparser
import datetime

from .base_template import BaseTemplate

class KriminalaParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.thread_name_pattern1 = re.compile(
            r'\!topic(\d+).*html'
        )
        self.thread_name_pattern2 = re.compile(
            r'\!viewtopic\.php.*?t=(\d+).*html'
        )

        super().__init__(*args, **kwargs)
        self.parser_name = kwargs.get('parser_name')
        self.date_pattern = re.compile(r'Добавлено:(.*)[ap]m', re.I)

        self.files = self.get_filtered_files(kwargs.get('files'))
        self.avatar_name_pattern = re.compile(r'avatars/(\w+\.\w+)$')
        self.comments_xpath = '//a[@name and @id]'
        self.header_xpath = '//a[@name and @id]'
        self.author_xpath = 'following-sibling::table[1]'\
            '//td[@class="nav"]/descendant::text()'
        self.title_xpath = '//h1/a[@class="maintitle"]/text()'
        self.avatar_xpath = 'following-sibling::table[2]//img[@class="avatar"]/@src'
        self.post_text_xpath = 'following-sibling::table[2]//td[@class="postbody"]/descendant::text()'
        self.index = 1
        # main function
        self.main()

    def get_filtered_files(self, files):
        filtered_files_1 = list(
            filter(
                lambda x: self.thread_name_pattern1.search(
                    x.split('/')[-1]) is not None,
                files
            )
        )
        filtered_files_2 = list(
            filter(
                lambda x: self.thread_name_pattern2.search(
                    x.split('/')[-1]) is not None,
                files
            )
        )
        sorted_files_1 = sorted(
            filtered_files_1,
            key=lambda x: int(self.thread_name_pattern1.search(
                x.split('/')[-1]).group(1)))
        sorted_files_2 = sorted(
            filtered_files_2,
            key=lambda x: int(self.thread_name_pattern2.search(
                x.split('/')[-1]).group(1)))
        return sorted_files_1 + sorted_files_2

    def get_date(self, tag):
        date = tag.xpath(
            'following-sibling::table[1]'
            '//span[@class="postdetails"]/text()'
        )
        if not date:
            date = tag.xpath(
                'following-sibling::table[1]'
                '//td[@nowrap and contains(string(), "Добавлено")]/text()'
            )
        if not date:
            return ''
        match = self.date_pattern.findall(date[-1])
        if not match:
            date = tag.xpath(
                'following-sibling::table[3]'
                '//span[@class="offcomment"]/text()'
            )
        if not date:
            return ''
        match = self.date_pattern.findall(date[-1])
        if not match:
            return ''
        date = match[0].strip()
        try:
            return str(datetime.datetime.strptime(str(dateparser.parse(date)), '%Y-%m-%d %H:%M:%S').timestamp())
        except:
            return ""

    def get_post_text(self, tag):
        post_text_block = tag.xpath(
            'following-sibling::table[2]//td[@class="postbody"]/descendant::text()'
        )
        if not post_text_block:
            return ''
        post_text = "\n".join([
            t.strip() for t in post_text_block if t.strip()
        ])
        return post_text if post_text else ''

    def extract_comments(self, html_response, pagination=None):
        comments = list()
        comment_blocks = html_response.xpath(
          '//a[@name and @id]'
        )
        comment_blocks = comment_blocks[1:] if self.index == 1\
            else comment_blocks
        for comment_block in comment_blocks:
            user = self.get_author(comment_block)
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            pid = self.thread_id
            avatar = self.get_avatar(comment_block)

            source = {
                'forum': self.parser_name,
                'pid': pid,
                'message': comment_text.strip(),
                'cid': str(self.index),
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
            self.index += 1
        return comments