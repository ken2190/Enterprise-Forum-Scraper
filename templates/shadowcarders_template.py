# -- coding: utf-8 --
import re
from .base_template import BaseTemplate


class ShadowCardersParser(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "shadowcarders.com"
        self.thread_name_pattern = re.compile(r"(\d+).*html")
        self.avatar_name_pattern = re.compile(r".*/(\S+\.\w+)")
        self.files = self.get_filtered_files(kwargs.get("files"))
        self.comments_xpath = '//ol[@class="messageList"]/li'
        self.header_xpath = '//ol[@class="messageList"]/li'
        self.date_xpath = (
            './/div[@class="privateControls"]'
            '//span[@class="DateTime"]/@title|'
            './/div[@class="privateControls"]'
            '//abbr[@class="DateTime"]/@data-datestring'
        )
        self.author_xpath = './/h3//a[@class="username"]//text()'
        self.title_xpath = '//div[@class="titleBar"]/h1/text()'
        self.post_text_xpath = (
            './/div//blockquote[contains(@class,"messageText")]//text()'
        )
        self.comment_block_xpath = './/div[@class="publicControls"]/a[1]/text()'
        self.avatar_xpath = './/a[@data-avatarhtml="true"]/img/@src'

        # main function
        self.main()
