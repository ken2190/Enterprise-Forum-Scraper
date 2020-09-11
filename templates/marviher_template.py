# -- coding: utf-8 --
import re
import utils

from .base_template import BaseTemplate

class MarviherParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "marviher.com"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.mode = 'r'
        self.comments_xpath = '//article[@id]'
        self.header_xpath = '//article[@id]'
        self.date_xpath = 'div//div[@class="ipsType_reset"]//time/@title'
        self.date_pattern = "%d.%m.%Y %H:%M"
        self.author_xpath = 'aside/h3/strong/a/text()'
        self.title_xpath = '//span[@class="ipsType_break ipsContained"]/span/text()'
        self.post_text_xpath = 'div//div[@data-role="commentContent"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'aside//li[@class="cAuthorPane_photo"]//a/img/@src'
        self.index = 1

        # main function
        self.main()

    def get_post_text(self, tag):
        post_text_block = tag.xpath(self.post_text_xpath)
        protected_email = tag.xpath(
            'div//div[@data-role="commentContent"]/'
            'descendant::*[@class="__cf_email__"]/@data-cfemail'
        )

        post_text = " ".join([
            post_text.strip() for post_text in post_text_block
        ])

        if protected_email:
            decoded_values = [
                utils.get_decoded_email(e) for e in protected_email]
            for decoded_value in decoded_values:
                post_text = re.sub(
                    r'\[email.*?protected\]',
                    decoded_value,
                    post_text,
                    count=1
                )

        return post_text.strip()
