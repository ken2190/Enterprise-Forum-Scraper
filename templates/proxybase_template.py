# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class ProxyBaseParser(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "http://proxy-base.com"
        self.avatar_name_pattern = re.compile(r".dateline=(\d+).")

        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.header_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.comment_block_xpath = 'table//td[2][@class="thead"]/a/strong//text()'
        self.post_text_xpath = 'table//tr[@valign="top"]/td[@class="alt1" and @id]/div[@id]/descendant::text()[not(ancestor::div[@style="margin:20px; margin-top:5px; "])]'

        self.date_xpath = 'table//td[1][@class="thead"]/a/following-sibling::text()'

        self.date_pattern = "%m/%d/%Y at %H:%M"
        self.title_xpath = 'table//tr[@valign="top"]/td[@class="alt1" and @id]/div[@class="smallfont"]/strong//text()'
        self.author_xpath = 'table//a[@class="bigusername"]//text()'
        self.avatar_xpath = './/td[1]//a[contains(@rel, "nofollow") and img]/img/@src'
        self.avatar_ext = 'jpg'
        self.mode = 'r+'

        self.main()
