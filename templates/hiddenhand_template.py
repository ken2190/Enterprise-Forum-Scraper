# -- coding: utf-8 --
import re
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class HiddenHandParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = kwargs.get('parser_name')
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="main-outlet"]/div[meta]'
        self.header_xpath = '//div[@id="main-outlet"]/div[meta]'
        self.author_xpath = 'div//b[@itemprop="author"]/text()'
        self.title_xpath = '//div[@id="main-outlet"]/h1/a/text()'
        self.post_text_xpath = 'div[@class="post"]/descendant::text()[not(ancestor::aside)]'
        self.avatar_xpath = 'div//li[@class="avatar"]/a/img/@src'
        self.comment_block_xpath = 'div//span[@itemprop="position"]/text()'
        self.date_pattern = "%Y-%m-%dT%H:%M:%SZ"

        # main function
        self.main()

    def extract_comments(self, html_response):
        comments = list()
        comment_blocks = html_response.xpath(self.comments_xpath)

        for index, comment_block in enumerate(comment_blocks[1:], 1):
            user = self.get_author(comment_block)
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            avatar = self.get_avatar(comment_block)
            pid = self.thread_id

            comment_id = self.get_comment_id(comment_block)
            if not comment_id or comment_id == "1":
                continue

            source = {
                'forum': self.parser_name,
                'pid': pid,
                'message': comment_text.strip(),
                'cid': comment_id,
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
        date_block = tag.xpath(
            'div//time[@itemprop="datePublished"]/@datetime'
        )
        if not date_block:
            date_block = tag.xpath(
                'div//meta[@itemprop="datePublished"]/@content'
            )
        date = date_block[0].strip() if date_block else ""

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
