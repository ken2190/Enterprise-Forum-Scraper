# -- coding: utf-8 --
import re
#import locale
import dateutil.parser as dparser

from .base_template import BaseTemplate

class CrackingSoulParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "crackingsoul.com"
        self.avatar_name_pattern = re.compile(r'avatar_(\d+\.\w+)')
        self.mode = 'r'
        self.comments_xpath = '//div[@id="posts"]/div[contains(@class,"post ")]'
        self.header_xpath = '//div[@id="posts"]/div[contains(@class,"post ")]'
        self.date_xpath = './/span[@class="post_date"]/text()'
        self.title_xpath = '//span[@class="active"]//text()'
        self.post_text_xpath = './/div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.comment_block_xpath = './/div[@class="post_head"]/div/strong/a/text()'
        self.avatar_xpath = './/div[@class="author_avatar"]/a/img/@src'
        self.author_xpath = './/div[contains(@class,"author_information")]//strong//text()'

        # main function
        self.main()
