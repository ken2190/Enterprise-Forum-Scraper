# -- coding: utf-8 --
import re
import dateutil.parser as dparser

from .base_template import BaseTemplate


class NulledBBParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "nulledbb.com"
        self.avatar_name_pattern = re.compile(r'.*avatar_(\d+\.\w+)')
        self.comments_xpath = '//div[@class="wrapper"]/div[1][@class="table-wrap"]'
        self.header_xpath = '//div[@class="wrapper"]/div[1][@class="table-wrap"]'
        self.date_xpath = 'div//div[contains(string(), "Posted:")]/text()'
        self.title_xpath = '//div[@class="table-wrap"]//h1/text()'
        self.post_text_xpath = 'div//div[@class="postbit-message-content"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = 'div//div[@class="right"]/strong/a/text()'
        self.author_xpath = 'div//div[contains(@class, "postbit-username")]//span//text()'

        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = [d.strip() for d in date_block if d.strip()]
        if not date:
            return

        date = date[0].replace('Posted:', '').strip()
        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except:
            return ""
