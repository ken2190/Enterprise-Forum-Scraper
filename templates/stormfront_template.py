# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class StormFrontParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "stormfront.org"
        self.avatar_name_pattern = re.compile(
            r"u=(\d+)",
            re.IGNORECASE
        )
        self.mode = 'r'
        self.comments_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.header_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.date_xpath = './/td[@class="thead"][1]/a[contains(@name,"post")]/following-sibling::text()[1]'
        self.author_xpath = './/a[@class="bigusername"]/descendant::text()|'\
                            './/div[contains(@id,"postmenu")]/text()'
        self.title_xpath = '//span[@itemprop="title"]/text()'
        self.post_text_xpath = './/div[contains(@id, "post_message")]/descendant::text()[not(ancestor::div[@style="margin:20px; margin-top:5px; "])]'
        self.avatar_xpath = '//a[contains(@href, "member.php?") and img/@src]/@href'
        self.comment_block_xpath = './/a[contains(@id,"postcount")]/@name'

        # main function
        self.main()
