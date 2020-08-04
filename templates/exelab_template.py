# -- coding: utf-8 --
import re
# import locale
import traceback
import utils
import dateparser

from .base_template import BaseTemplate


class ExelabParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "exelab.ru"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.mode = 'r'
        self.comments_xpath = '//table[contains(@class,"forums")][2]/tr[contains(@class,"tbCel")]'
        self.header_xpath = '//table[contains(@class,"forums")][2]/tr[contains(@class,"tbCel")]'
        self.date_xpath = './/td[2]//span[@class="txtSm"]//text()'
        self.title_xpath = '//span[@class="header"][1]/text()'
        self.post_text_xpath = './/td[2]/div//text()[not(ancestor::i)]'
        self.avatar_xpath = './/div[@class="username"]//img[2]/@src'
        self.comment_block_xpath = './/span[@class="txtSm"]//a//text()'

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
            key=lambda x: (self.thread_name_pattern.search(x).group(1),
                           self.pagination_pattern.search(x).group(1)))

        return sorted_files

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)[0]

        date_block = ' '.join(date_block.split(' ')[1:]).split('·')[0]
        date = date_block.strip() if date_block else ""
        try:
            date = dateparser.parse(date).timestamp()
            return str(date)
        except:
            # traceback.print_exc()
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            './/div[contains(@class,"username")]//a//text()'
        )[0]
        if not author:
            author = tag.xpath(
                './/div[contains(@class,"post_author")]/a/span//text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]/strong//b/span/text()'
            )

        author = author.strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)[:5]
        title = ''.join(title)
        title = title.strip() if title else None

        return title

    def get_post_text(self, tag):
        post_text_block = tag.xpath(self.post_text_xpath)
        post_text = "".join([
            post_text.strip() for post_text in post_text_block
        ])

        return post_text[2:].strip()

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        comment_block = ''.join(comment_block)

        if comment_block:
            comment_id = comment_block.split('#')[-1]

        return comment_id.replace(',', '')
