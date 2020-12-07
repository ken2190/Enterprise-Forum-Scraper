# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class CrackingProParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "crackingpro.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.index = 1
        self.comments_xpath = '//article[contains(@id, "elComment_")]'
        self.header_xpath = '//article[contains(@id, "elComment_")]'
        self.date_xpath = 'div//div[@class="ipsType_reset"]//time/@title'
        self.title_xpath = '//span[@class="ipsType_break ipsContained"]/span/text()'
        self.post_text_xpath = 'div//div[@data-role="commentContent"]/descendant::text()[not(ancestor::blockquote)]'
        self.mode = 'r'

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
            key=lambda x: (int(self.thread_name_pattern.search(x).group(1)),
                           int(self.pagination_pattern.search(x).group(1))))

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
        author = tag.xpath(
            'aside//a[@class="ipsType_break"]/span/span/text()'
        )
        if not author:
            author = tag.xpath(
                'aside//a[@class="ipsType_break"]/span/text()'
            )
        if not author:
            author = tag.xpath(
                'aside//a[@class="ipsType_break"]/text()'
            )
        if not author:
            author = tag.xpath(
                'aside//div[contains(@class, "lkComment_author")]/descendant::text()'
            )
        if not author:
            author = tag.xpath(
                './/h3[contains(@class, "cAuthorPane_author")]/strong/text()'
            )
        author = ' '.join(author).strip() if author else None

        return author

    def get_avatar(self, tag):
        avatar_block = tag.xpath(
            'aside//li[@class="cAuthorPane_photo"]/div/a/img/@src'
        )
        if not avatar_block:
            return ""

        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""

        if name_match[0].startswith('svg'):
            return ''

        return name_match[0]
