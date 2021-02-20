# -- coding: utf-8 --
import re
import locale

from .base_template import BaseTemplate


class VerifiedCarderParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        super().__init__(*args, **kwargs)
        self.parser_name = "verifiedcarder.ws"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//article[contains(@class, "ipsComment")]'
        self.header_xpath = '//article[contains(@class, "ipsComment")]'
        self.date_xpath = './/div[contains(@class, "ipsComment_meta")]//time/@datetime'
        self.title_xpath = '//h1[contains(@class, "ipsType_pageTitle")]//text()'
        self.post_text_xpath = '//div[contains(@class, "cPost_contentWrap")]//text()'
        self.avatar_xpath = '//img[contains(@class, "ipsUserPhoto")]/@src'
        self.author_xpath = '//a[contains(@class, "ipsType_break")]/text()'
        self.index = 1
        self.main()
        # main function
    
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
