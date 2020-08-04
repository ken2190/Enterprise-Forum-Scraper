# -- coding: utf-8 --
import re
import utils

from .base_template import BaseTemplate


class HoxForumParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = kwargs.get('parser_name')
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[contains(@class,"post classic")]'
        self.header_xpath = '//div[contains(@class,"post classic")]'
        self.date_xpath = 'div//span[@class="post_date"]/text()'
        self.author_xpath = 'div//div[@class="author_information"]//span/a/text()'
        self.title_xpath = '//td[@class="thead"]/div/strong/text()'
        self.avatar_xpath = '//div[contains(@class, "author_avatar")]/a/img/@src'
        self.avatar_ext = 'jpg'
        self.comment_block_xpath = 'div//div[@class="post_head"]//strong/a/text()'

        # main function
        self.main()

    def get_post_text(self, tag):
        post_text_block = tag.xpath(
            'div//div[@class="post_body scaleimages"]'
            '/descendant::text()[not(ancestor::blockquote)]'
        )
        protected_email = tag.xpath(
            'div//div[@class="post_body scaleimages"]/'
            'descendant::*[@class="__cf_email__"]/@data-cfemail'
        )
        post_text = "".join([
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

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        if comment_block:
            comment_id = comment_block[-1].strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')
