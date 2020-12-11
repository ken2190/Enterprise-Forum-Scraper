# -- coding: utf-8 --
import re
import dateparser

from .base_template import BaseTemplate


class NulledBBParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "nulledbb.com"
        self.avatar_name_pattern = re.compile(r'.*avatar_(\d+\.\w+)')
        self.comments_xpath = '//div[@class="wrapper"]/div[1][@class="table-wrap"]'
        self.header_xpath = '//div[@class="wrapper"]/div[1][@class="table-wrap"]'
        self.date_xpath_1 = 'div//div[contains(string(), "Posted:")]/text()'
        self.date_xpath_2 = 'div//div[contains(string(), "Posted:")]/span[@title]/@title|'\
            'div//div[contains(string(), "Posted:")]/span[@title]/following-sibling::text()[1]'
        self.title_xpath = '//div[@class="table-wrap"]//h1/text()'
        self.post_text_xpath = 'div//div[@class="postbit-message-content"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = 'div//div[@class="right"]/strong/a/text()'
        self.author_xpath = 'div//div[contains(@class, "postbit-username")]//span//text()|'\
            'div//div[contains(@class, "postbit-username")]//a//text()'

        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath_1)
        date = [d.strip() for d in date_block if d.strip()]
        if not date:
            return

        date = date[0].replace('Posted:', '').strip()
        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except:
            return ""

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath_1)
        date = [d.strip() for d in date_block if d.strip()]
        date = date[0].replace('Posted:', '').strip()

        if not date:
            date_block = tag.xpath(self.date_xpath_2)
            date = ''.join(date_block)
            print(date)

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
