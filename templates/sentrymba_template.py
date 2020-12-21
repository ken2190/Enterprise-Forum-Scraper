# -- coding: utf-8 --
import re
import dateparser

from .base_template import BaseTemplate


class SentryMBAParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "sentry.mba"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="posts"]/div[@class="postbit"]'
        self.header_xpath = '//div[@id="posts"]/div[@class="postbit"]'
        self.date_xpath_1 = './/div[@class="head"]/text()'
        self.date_xpath_2 = './/div[@class="head"]/span/@title'
        self.date_pattern = '%m-%d-%Y, %I:%M %p'
        self.author_xpath = './/div[@class="style"]//strong/text()|'\
            './/div[@class="style"]//strong//text()|'\
            './/div[@class="style"]/text()'
        self.title_xpath = '//div[@class="subject"]/text()'
        self.post_text_xpath = 'div[@class="content"]/div[@class="text scaleimages post_body scaleimages"]/text()'
        self.comment_block_xpath = 'div/div[@class="head"]/div[@class="right"]/a/text()'
        self.avatar_xpath = 'div//img[@class="avatarp radius100"]/@src'

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
                           x.split("-")[-1]))
        return sorted_files
        
    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if not author:
            author = tag.xpath(
                'div//div[@class="uix_userTextInner"]'
                '/a[@class="username"]/span/text()'
            )

        author = author[0].strip() if author else None
        return author

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
