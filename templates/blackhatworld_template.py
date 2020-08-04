# -- coding: utf-8 --
import re
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class BlackHatWorldParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "blackhatworld.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath =  '//ol[@class="messageList"]/li'
        self.header_xpath = '//ol[contains(@class, "messageList")]/li'
        self.date_xpath = 'div//a[@class="datePermalink"]/span/@title'
        self.date_pattern = "%b %d, %Y at %I:%M %p"
        self.author_xpath = '@data-author'
        self.title_xpath = '//div[@class="titleBar"]/h1/text()'
        self.comment_block_xpath = 'div//div[@class="publicControls"]/a/text()'
        self.avatar_xpath = 'div//div[@class="avatarHolder"]/a/img/@src'

        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        if not date_block:
            date_block = tag.xpath(
                'div//a[@class="datePermalink"]'
                '/abbr/text()'
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

    def get_post_text(self, tag):
        post_text_block = tag.xpath(
            'div//div[@class="messageContent"]/article/blockquote/'
            'descendant::text()['
            'not(ancestor::div[@class="bbCodeBlock bbCodeQuote"])]'
        )

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
