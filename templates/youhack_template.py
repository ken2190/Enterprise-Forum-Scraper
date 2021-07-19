# -- coding: utf-8 --
import re
import utils

from .base_template import BaseTemplate


class YouHackParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "youhack.ru"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//ol[@class="messageList"]/li[contains(@id, "post-")]'
        self.header_xpath = '//ol[@class="messageList"]/li[contains(@id, "post-")]'
        self.date_xpath = './/*[contains(@class,"DateTime")]/@data-time|' \
                          './/*[contains(@class,"DateTime")]/@title'
        self.date_pattern = '%d.%m.%Y at %I:%M %p'
        self.author_xpath = '@data-author'
        self.title_xpath = '//div[@class="titleBar"]/h1/text()'
        self.post_text_xpath = 'div//div[@class="messageContent"]/article/blockquote/descendant::text()[not(ancestor::div[@class="bbCodeBlock bbCodeQuote"])]'
        self.avatar_xpath = 'div//div[@class="avatarHolder"]/a/img/@src'
        self.comment_block_xpath = 'div//div[@class="publicControls"]/a/text()'
        self.offset_hours = -3

        # main function
        self.main()

    def get_post_text(self, tag):
        post_text_block = tag.xpath(self.post_text_xpath)
        protected_email = tag.xpath(
            'div//div[@class="messageContent"]/article/blockquote/'
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

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date_string = date_block[0].strip() if date_block else None
        date = self.parse_date_string(date_string)
        return date