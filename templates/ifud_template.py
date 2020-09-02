# -- coding: utf-8 --
import re
import utils

from .base_template import BaseTemplate


class IfudParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "http://ifud.ws"
        self.thread_name_pattern = re.compile(
            r'(\d+)-\d+\.html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r".*/(\S+\.\w+)")
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//article[contains(@class,"message--post")]'
        self.header_xpath = '//article[contains(@class,"message--post")]'
        self.date_xpath = 'div//div[@class="message-attribution-main"]/a/time/@data-time'
        self.author_xpath = './/div[@class="message-userDetails"]/h4/a/descendant::text()'
        self.title_xpath = '//h1[@class="p-title-value"]/text()'
        self.comment_block_xpath = 'div//ul[@class="message-attribution-opposite message-attribution-opposite--list"]/li/a/text()'
        self.avatar_xpath = 'div//div[@class="message-avatar-wrapper"]/a[img/@src]/img/@src'
        self.mode = 'r'

        # main function
        self.main()


    def get_post_text(self, tag):
        post_text_block = tag.xpath(
            'div//article/div[@class="bbWrapper"]'
            '/descendant::text()[not(ancestor::div'
            '[contains(@class, "bbCodeBlock bbCodeBlock--expandable '
            'bbCodeBlock--quote")])]'
        )
        protected_email = tag.xpath(
            'div//article/div[@class="bbWrapper"]/'
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
