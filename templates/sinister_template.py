# -- coding: utf-8 --
import datetime
import re
import dateparser

from .base_template import BaseTemplate


class SinisterParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "sinister.ly"
        self.avatar_name_pattern = re.compile(r'(\d+\.\w+)')
        self.comments_xpath = '//div[@id="posts"]/div'
        self.header_xpath = '//div[@id="posts"]/div'
        self.date_xpath_1 = 'div//span[@class="post_date postbit_date"]/text()'
        self.date_xpath_2 = 'div//span[@class="post_date postbit_date"]/span/@title'
        self.date_pattern = "%m-%d-%Y, %I:%M %p"
        self.author_xpath = 'div//span[@class="largetext postbit_username"]/a/span/text()'
        self.title_xpath = '//table//strong/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = './/div[contains(@class,"author_avatar")]//img/@src'
        self.comment_block_xpath = 'div//span[@class="post_date postbit_date"]/following-sibling::a[1]/text()'

        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath_1)
        date = date_block[0].strip() if date_block else None

        if not date:
            date_block = tag.xpath(self.date_xpath_2)
            date = date_block[0].strip() if date_block else None

        # check if date is already a timestamp
        try:
            date = datetime.datetime.strptime(date, self.date_pattern).timestamp()
            return str(date)
        except:
            try:
                date = float(date)
                return date
            except:
                try:
                    date = dateparser.parse(date).timestamp()
                    return str(date)
                except:
                    pass

        return ""
