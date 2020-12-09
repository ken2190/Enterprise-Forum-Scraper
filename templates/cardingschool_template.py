# -- coding: utf-8 --
import re
import utils

from .base_template import BaseTemplate


class CardingSchoolParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "carding.school"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//article[@id]'
        self.header_xpath = '//article[@id]'
        self.date_xpath = 'div//div[@class="ipsType_reset"]//time/@title'
        self.date_pattern = "%d.%m.%Y %H:%M"
        self.author_xpath = 'aside/h3/strong/a/text()'
        self.title_xpath = '//span[@class="ipsType_break ipsContained"]/span/text()'
        self.comment_block_xpath =  'div//div[@class="publicControls"]/a/text()'
        self.avatar_xpath = 'aside//li[@class="cAuthorPane_photo"]//a/img/@src'
        self.mode = 'r'

        # main function
        self.main()

    def extract_comments(self, html_response, pagination):
        comments = list()
        comment_blocks = html_response.xpath(self.comments_xpath)

        for index, comment_block in enumerate(comment_blocks[1:], 1):
            user = self.get_author(comment_block)
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            pid = self.thread_id
            avatar = self.get_avatar(comment_block)
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

    def get_post_text(self, tag):
        post_text_block = tag.xpath(
            'div//div[@data-role="commentContent"]/descendant::text()['
            'not(ancestor::blockquote)]'
        )
        protected_email = tag.xpath(
            'div//div[@data-role="commentContent"]/'
            'descendant::*[@class="__cf_email__"]/@data-cfemail'
        )
        post_text = " ".join([
            post_text.strip() for post_text in post_text_block
        ])

        if protected_email:
            decoded_values = [utils.get_decoded_email(e) for e in protected_email]
            for decoded_value in decoded_values:
                post_text = re.sub(
                    r'\[email.*?protected\]',
                    decoded_value,
                    post_text,
                    count=1
                )

        return post_text.strip()
