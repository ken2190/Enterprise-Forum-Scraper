# -- coding: utf-8 --
import re
import traceback
# import locale
import utils
import dateutil.parser as dparser

from .base_template import BaseTemplate


class DarkwayParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "darkway_kzx2d7tcvfm5j6yt2ii7ejkeal3d5oy5gsewwnw7hmywj3nordbg4syd"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.index = 1
        self.mode = 'r'
        self.comments_xpath = '//section[contains(@class,"post ")]'
        self.header_xpath = '//section[contains(@class,"post ")]'
        self.date_xpath = './/time/text()'
        self.post_text_xpath = './/article[@class="postText"]//text()'
        self.author_xpath = './/a[@class="userLink"]/text()'
        self.title_xpath = '//header[@class="topicHeader"]/h3/a/text()'
        self.avatar_xpath = './/img[contains(@class,"avatar")]/@src'

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

    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        author = author[-1].strip() if author else None

        return author

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = title[0].strip().split(']')[-1] if title else None

        return title

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
