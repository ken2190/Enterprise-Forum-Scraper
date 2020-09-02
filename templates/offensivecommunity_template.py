# -- coding: utf-8 --
import re
#import locale
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class OffensiveCommunityParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "offensivecommunity.net"
        self.thread_name_pattern = re.compile(
            r'(.*)-\d+\.html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(
            r".*/(\d+\.\w+)",
            re.IGNORECASE
        )
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.mode = 'r'
        self.comments_xpath = '//div[@id="posts"]/table'
        self.header_xpath = '//div[@id="posts"]/table'
        self.date_xpath = './/td[@class="tcat"]/div[1]/text()'
        self.author_xpath = './/td[@class="post_author"]//span[@class="largetext"]//a/text()'
        self.post_text_xpath = './/td[contains(@class,"post_content")]//text()'
        self.avatar_xpath = './/td[contains(@class,"post_avatar")]//img/@src'
        self.title_xpath = '//table[@class="tborder tfixed clear"]//td[@class="thead"]//strong/text()'
        self.comment_block_xpath = './/span[@class="smalltext"]/strong/a/text()'
        self.index = 1

        # main function
        self.main()