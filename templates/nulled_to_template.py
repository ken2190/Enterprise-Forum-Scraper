# -- coding: utf-8 --
import re
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class NulledToParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "nulled.to"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[contains(@id, "post_id_")]/div[@class="post_wrap"]'
        self.header_xpath = '//div[contains(@id, "post_id_")]/div[@class="post_wrap"]'
        self.date_xpath = 'div/div[@class="post_date"]/abbr/@title'
        self.date_pattern = "%Y-%m-%dT%H:%M:%S"
        self.author_xpath = 'div[@class="author_info clearfix"]//span[@class="author vcard"]/a/span/span/text()'
        self.title_xpath = '//div[@class="maintitle clear clearfix"]/span/text()'
        self.post_text_xpath = 'div//section[@id="nulledPost"]'
        self.avatar_xpath = 'div//li[@class="avatar"]/img/@src'
        self.comment_block_xpath = 'div//a[@itemprop="replyToUrl"]/text()'
        self.avatar_name_pattern = re.compile(
            r".*/profile/photo-(\d+\.\w+)\?.*",
            re.IGNORECASE
        )

        # main function
        self.main()

    def get_date(self, tag):
        date = tag.xpath(self.date_xpath)
        date = date[0].split('+')[0].strip() if date else ""

        try:
            date = datetime.datetime.strptime(date, self.date_pattern).timestamp()
            return str(date)
        except:
            try:
                date = dparser.parse(date).timestamp()
                return str(date)
            except :
                pass

        return ""

    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if not author:
            author = tag.xpath(
                'div[@class="author_info clearfix"]'
                '//span[@class="author vcard"]/s/text()'
            )
        if not author:
            author = tag.xpath(
                'div[@class="author_info clearfix"]'
                '/div[@class="post_username"]/text()'
            )
        if not author:
            author = tag.xpath(
                'div[@class="author_info clearfix"]'
                '//span[@class="author vcard"]/descendant::text()'
            )

        author = ''.join(author).strip() if author else None
        return author

    def get_post_text(self, tag):
        post_text_block = tag.xpath(self.post_text_xpath)
        post_text = "\n".join([
            post_text.xpath('string()') for post_text in post_text_block
        ])

        return post_text.strip()
