# -- coding: utf-8 --
import re
import dateparser

from .base_template import BaseTemplate


class CrackXParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "crackx.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//article[contains(@class,"post-set")]'
        self.header_xpath = '//article[contains(@class,"post-set")]'
        self.date_xpath_1 = 'div//span[contains(@class, "post_date")]/text()'
        self.date_xpath_2 = 'div//span[contains(@class, "post_date")]/span[1]/@title'
        self.date_pattern = '%m-%d-%Y, %I:%M %p'
        self.author_xpath = 'div//div[contains(@class,"post-username")]/a//text()'
        self.title_xpath = '//div[@class="thread-header"]/h1/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.comment_block_xpath = 'div//div[@class="right postbit-number"]/strong/a/text()'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'

        # main function
        self.main()

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)

        if comment_block:
            comment_id = comment_block[-1].strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath_1)
        date = date_block[0].strip() if date_block else None

        if not date:
            date_block = tag.xpath(self.date_xpath_2)
            date = date_block[0].strip() if date_block else None

        # check if date is already a timestamp
        try:
            date = dateparser.parse(date).timestamp()
            return str(date)
        except:
            try:
                date = float(date)
                return date
            except:
                try:
                    date = datetime.datetime.strptime(date, self.date_pattern).timestamp()
                    return str(date)
                except:
                    pass

        return ""