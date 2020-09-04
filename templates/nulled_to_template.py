# -- coding: utf-8 --
import re
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class NulledToParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "nulled.to"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//div[contains(@id, "post_id_")]/div[@class="post_wrap"]'
        self.header_xpath = '//div[contains(@id, "post_id_")]/div[@class="post_wrap"]'
        self.date_xpath = 'div/div[@class="post_date"]/abbr/@title'
        self.author_xpath = 'div[@class="author_info clearfix"]//span[@class="author vcard"]/a/span/span/text()'
        self.title_xpath = '//div[@class="maintitle clear clearfix"]/span/text()'
        self.post_text_xpath = 'div//section[@id="nulledPost"]/descendant::text()'
        self.avatar_xpath = 'div//li[@class="avatar"]/img/@src'
        self.comment_block_xpath = 'div//a[@itemprop="replyToUrl"]/text()'
        self.avatar_name_pattern = re.compile(
            r".*/profile/photo-(\d+\.\w+)\?.*",
            re.IGNORECASE
        )

        # main function
        self.main()
