# -- coding: utf-8 --
import re
import utils

from .base_template import BaseTemplate


class GerkiParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "https://gerki.pw"
        self.thread_name_pattern = re.compile(
            r'(\d+)-\d+\.html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r".*/(\S+\.\w+)")
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@class="message-inner"]'
        self.header_xpath = '//div[@class="message-inner"]'
        self.date_xpath = 'div//div[@class="message-attribution-main"]/a/time/@data-time'
        self.author_xpath = './/div[contains(@class,"message-userDetails")]//span[contains(@class,"username")]/descendant::text()'
        self.title_xpath = '//h1[@class="p-title-value"]/text()'
        self.comment_block_xpath = 'div//ul[@class="message-attribution-opposite message-attribution-opposite--list"]/li/a/text()'
        self.avatar_xpath = 'div//div[@class="message-avatar-wrapper"]/a[img/@src]/@href'
        self.avatar_ext = 'jpg'
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
            key=lambda x: (
                int(self.thread_name_pattern.search(x).group(1)),
                int(self.pagination_pattern.search(x).group(1))
            )
        )

        return sorted_files

    def get_date(self, tag):
        date = tag.xpath(self.date_xpath)
        return date[0] if date else ''

    def get_author(self, tag):
        author_block = tag.xpath(self.author_xpath)
        author = " ".join([
            author.strip() for author in author_block
        ])
        protected_email = tag.xpath(
            './/div[@class="message-userDetails"]/h4/a/'
            'descendant::*[@class="__cf_email__"]/@data-cfemail'
        )
        if protected_email:
            decoded_values = [
                utils.get_decoded_email(e) for e in protected_email
            ]
            for decoded_value in decoded_values:
                author = re.sub(
                    r'\[email.*?protected\]',
                    decoded_value,
                    author,
                    count=1
                )

        return author

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

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        if comment_block:
            comment_id = comment_block[-1].strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')
