# -- coding: utf-8 --
import re
# import locale
import utils

from .base_template import BaseTemplate


class CrackedToParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "cracked.to"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[contains(@class, "post-box")]'
        self.header_xpath = '//div[contains(@class, "post-box")]'
        self.date_xpath = './/span[@class="post_date"]//@title'
        self.date_pattern = "%H:%M %p - %d %B, %Y"
        self.title_xpath = '//div[@class="thread-header"]/h1/text()'
        self.comment_block_xpath = './/span[contains(@class, "posturl")]//strong/a/text()'
        self.avatar_xpath = './/div[@class="post-avatar"]//a/img/@src'

        # main function
        self.main()

    def get_author(self, tag):
        author = tag.xpath(
            './/div[@class="post-username"]/span/a/text()'
        )
        if not author:
            author = tag.xpath(
                './/div[@class="post-username"]/span/a/s/text()'
            )
        if not author:
            author = tag.xpath(
                './/div[@class="post-username"]/span/a/span/text()'
            )
        if not author:
            author = tag.xpath(
                './/div[@class="post-username"]/span/a/strong/span/text()'
            )
        if not author:
            author = tag.xpath(
                './/div[@class="post-username"]/span/text()'
            )

        author = author[0].strip() if author else None
        return author

    def get_post_text(self, tag):
        post_text_block = tag.xpath(
            './/div[starts-with(@id, "pid_")]/text()'
        )
        protected_email = tag.xpath(
            './/div//div[@class="post_body scaleimages"]/'
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
