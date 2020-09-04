# -- coding: utf-8 --
import re
import dateutil.parser as dparser

from .base_template import BaseTemplate


class OgUsersParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "ogusers.com"
        self.avatar_name_pattern = re.compile(r".*avatar_(\d+\.\w+)\?")
        self.mode = 'r'
        self.comments_xpath = '//div[@class="postbox"]'
        self.header_xpath = '//div[@class="postbox"]'
        self.date_xpath = 'div//div[contains(@class,"pb_date")]/span/@title'\
                          '|div//div[contains(@class,"pb_date")]/text()'
        self.title_xpath = '//span[@class="showthreadtopbar_size"]/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'aside//div[@class="postbit-avatar"]/a/img/@src|.//img[@class="profileshow"]/@src'
        self.comment_block_xpath = 'div//div[@class="float_right postbitnum"]/strong/a/text()'
        self.author_xpath = 'aside//div[contains(@class,"postbitdetail")]/span//text()'
        self.date_xpath = 'div//div[contains(@class,"pb_date")]/text()'

        # main function
        self.main()
