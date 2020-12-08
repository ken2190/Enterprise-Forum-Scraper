# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class OmertaParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "omerta.cc"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'(\w+)\'s ')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.mode = 'r'
        self.comments_xpath = '//table[contains(@id, "post")]'
        self.header_xpath = '//table[contains(@id, "post")]'
        self.date_xpath = 'tr//a[contains(@name, "post")]/following-sibling::text()'
        self.date_pattern = '%m-%d-%Y, %I:%M %p'
        self.title_xpath = '//td[@class="navbar"]/a/strong/text()'
        self.post_text_xpath = 'tr//div[contains(@id, "post_message_")]/descendant::text()[not(ancestor::div[@style="margin:20px; margin-top:5px; "])]'
        self.avatar_xpath = 'tr//a[contains(@href, "member.php")]/img[@src]/@alt'
        self.avatar_ext = 'jpg'
        self.comment_block_xpath = 'tr//a[contains(@id, "postcount")]/strong/text()'

        # main function
        self.main()

    def get_author(self, tag):
        author = tag.xpath(
            'tr//a[@class="bigusername"]/text()'
        )
        if not author:
            author = tag.xpath(
                'tr//a[@class="bigusername"]/strike/text()'
            )
        if not author:
            author = tag.xpath(
                'tr//a[@class="bigusername"]/font/text()'
            )

        if not author:
            author = tag.xpath(
                'tr//a[@class="bigusername"]/font//text()'
            )

        if not author:
            author = tag.xpath(
                './/td[@class="alt2"]/div[1]/text()'
            )
        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        if not title:
            title = tag.xpath(
                '//td[@class="navbar"]/strong/text()'
            )

        title = title[0].strip() if title else None
        return title

    def get_comment_id(self, tag):
        comment_block = tag.xpath(self.comment_block_xpath)
        if not comment_block:
            return ''

        pattern = re.compile(r'\d+')
        match = pattern.findall(comment_block[0])
        if not match:
            return

        return match[0]
