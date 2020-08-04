# -- coding: utf-8 --
import re
import traceback
# import locale
import utils
import dateutil.parser as dparser

from .base_template import BaseTemplate


class EnvoyParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "http://envoys5appps3bin.onion"
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
        self.comments_xpath = '//div[contains(@class,"windowbg")]'
        self.header_xpath = '//div[contains(@class,"windowbg")]'
        self.date_xpath = './/div[@class="postarea"]//div[@class="keyinfo"]//div[@class="smalltext"]/text()[2]'
        self.author_xpath = './/div[@class="poster"]/h4/a/text()'
        self.post_text_xpath = './/div[@class="post"]/div/text()'
        self.avatar_xpath = './/img[@class="avatar"]/@src'
        self.title_xpath = '//h3[@class="catbg"]/text()'

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

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = date_block[0].split("»")[0].strip() if date_block else ""

        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except Exception:
            return ""

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

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)[2].split("Topic: ")[1].split("(")[0]
        title = title.strip().split(']')[-1] if title else None

        return title
