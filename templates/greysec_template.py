# -- coding: utf-8 --
import re
import dateparser

from .base_template import BaseTemplate


class GreySecParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "greysec.net"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="posts"]/div[contains(@class,"post")]'
        self.header_xpath = '//div[@id="posts"]/div[contains(@class,"post")]'
        self.date_xpath_1 = 'div//span[@class="post_date"]/text()'
        self.date_xpath_2 = 'div//span[@class="post_date"]/span/@title'
        self.date_pattern = '%m-%d-%Y, %I:%M %p'
        self.title_xpath = '//td[@class="thead"]/div/strong/text()'
        self.comment_block_xpath = 'div//div[@class="post_head"]//a/text()'
        self.avatar_xpath = '//div[@id="posts"]/div[contains(@class,"post")]//div[@class="author_avatar"]//img/@src'

        # main function
        self.main()

    def get_author(self, tag):
        author = tag.xpath(
            'div//div[@class="author_information"]'
            '//span[@class="largetext"]//strong/text()'
        )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]'
                '//span[@class="largetext"]/a/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]'
                '//span[@class="largetext"]/a/span/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]'
                '//span[@class="largetext"]/a/s/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]'
                '//span[@class="largetext"]/descendant::text()'
            )

        author = author[0].strip() if author else None
        return author

    def get_post_text(self, tag):
        post_text = tag.xpath(
            'div//div[@class="post_body scaleimages"]/text()'
        )

        post_text = "\n".join(
            [text.strip() for text in post_text if text.strip()]
        ) if post_text else ""

        if not post_text:
            post_text = tag.xpath(
                'div//blockquote[contains(@class,"messageText")]'
                '/span/div/text()'
            )

            post_text = "\n".join(
                [text.strip() for text in post_text if text.strip()]
            ) if post_text else ""

        return post_text.strip()

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