# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class DigitalGangsterParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "digitalgangster.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.mode = 'r'
        self.index = 1
        self.comments_xpath = '//div[@id="page-body"]/div[contains(@class, "post ")]'
        self.header_xpath = '//div[@id="page-body"]/div[contains(@class, "post ")]'
        self.date_xpath = './/p[@class="author"]//time/text()'
        self.author_xpath = './/p[@class="author"]//a[contains(@class,"username")]/text()'
        self.title_xpath = './/h2[@class="topic-title"]/a/text()'
        self.post_text_xpath = './/div[@class="content"]//text()[not(ancestor::blockquote)]'
        self.avatar_xpath = './/img[@class="avatar"]/@src'

        # main function
        self.main()

    def get_pid(self):
        pid_pattern = re.compile(r'topic[=,](\d+)')
        pid = pid_pattern.findall(self.thread_id)
        pid = pid[0] if pid else self.thread_id

        return pid

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

    def extract_comments(self, html_response, pagination):
        comments = list()
        comment_blocks = html_response.xpath(self.comments_xpath)

        comment_blocks = comment_blocks[1:]\
            if pagination == 1 else comment_blocks

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

    def get_avatar(self, tag):
        avatar_block = tag.xpath(self.avatar_xpath)
        if not avatar_block:
            return ""

        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""

        if name_match[0].startswith('svg'):
            return ''

        return name_match[0]
