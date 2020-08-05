# -- coding: utf-8 --
import re
import dateutil.parser as dparser

from .base_template import BaseTemplate


class LeakPortalParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "leakportal.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.mode = 'r'
        self.comments_xpath = '//article[@id]'
        self.header_xpath = '//article[@id]'
        self.date_xpath = 'div//div[@class="ipsType_reset"]//time/@title'
        self.author_xpath = 'aside/h3/strong/a/text()'
        self.title_xpath = '//span[@class="ipsType_break ipsContained"]/span/text()'
        self.post_text_xpath = 'div//div[@data-role="commentContent"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'aside//li[@class="cAuthorPane_photo"]/img/@src'

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

    def extract_comments(self, html_response, pagination):
        comments = list()
        comment_blocks = html_response.xpath(self.comments_xpath)

        comment_blocks = comment_blocks[1:]\
            if pagination == 1 else comment_blocks

        for comment_block in comment_blocks:
            user = self.get_author(comment_block)
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            avatar = self.get_avatar(comment_block)
            pid = self.thread_id

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
        date = date_block[0].strip() if date_block else ""

        try:
            date = dparser.parse(date, fuzzy=True).timestamp()
            return str(date)
        except:
            return ""

    def get_avatar(self, tag):
        avatar_block = tag.xpath(self.avatar_xpath)
        if not avatar_block:
            return ""

        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""

        return name_match[0] if 'svg' not in name_match[0] else ''
