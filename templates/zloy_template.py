# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class ZloyParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "zloy.bz"
        self.avatar_name_pattern = re.compile(r"u=(\d+)")
        self.mode = 'r'
        self.comments_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.header_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.date_xpath = 'table//td[1][@class="thead"]/a/following-sibling::text()'
        self.date_pattern = "%d.%m.%Y, %H:%M"
        self.title_xpath = 'table//tr[@valign="top"]/td[@class="alt1" and @id]/div[@class="smallfont"]/strong/text()'
        self.post_text_xpath = 'table//tr[@valign="top"]/td[@class="alt1" and @id]/div[@id]/descendant::text()[not(ancestor::div[@style="margin:20px; margin-top:5px; "])]'
        self.avatar_xpath = 'table//a[contains(@href, "member.php")]//img/@src'
        self.comment_block_xpath = 'table//td[2][@class="thead"]/a/strong/text()'
        self.author_xpath = 'table//a[@class="bigusername"]//text()|table//div[contains(@id, "postmenu_")]//text()'
        self.avatar_ext = 'jpg'

        # main function
        self.main()
