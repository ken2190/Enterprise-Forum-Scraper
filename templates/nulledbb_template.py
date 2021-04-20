# -- coding: utf-8 --
import re
import dateparser
import datetime

from .base_template import BaseTemplate


class NulledBBParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "nulledbb.com"
        self.avatar_name_pattern = re.compile(r'.*avatar_(\d+\.\w+)')
        self.comments_xpath = '//article[contains(@class, "post")]'
        self.header_xpath = '//article[contains(@class, "post")]'
        self.date_pattern = '%d-%m-%Y, %I:%M %p'
        self.date_xpath = './/div[@class="flex-fill"]/span[@data-toggle]/text()'
        self.title_xpath = '//h1[contains(@itemprop, "headline")]/text()'
        self.post_text_xpath = './/div[@itemprop="articleBody"]//text()'
        self.avatar_xpath = './/a[contains(@class,"post-avatar")]/img/@src'
        self.comment_block_xpath = './/a[@class="mt-n1"]/text()'
        self.author_xpath = './/div[contains(@class, "post-username")]//text()'

        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = [d.strip() for d in date_block if d.strip()]
        if not date:
            return

        date = date[0].replace('Posted:', '').strip()
        try:
            date = datetime.datetime.strptime(date, self.date_pattern).timestamp()
            return str(date)
        except:
            try:
                date = dateparser.parse(date).timestamp()
                return str(date)
            except:
                return ""