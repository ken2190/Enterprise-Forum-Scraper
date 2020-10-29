import re
from .base_template import BaseTemplate


class BinrevParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "binrev.com"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.index = 1
        self.comments_xpath = '//article[contains(@id, "elComment_")]'
        self.header_xpath = '//article[contains(@id, "elComment_")]'
        self.date_xpath = './/time/@title'
        self.author_xpath = 'aside//a[@class="ipsType_break"]//text()'
        self.title_xpath = '//div[@class="ipsType_break ipsContained"]/span/text()'
        self.post_text_xpath = 'div//div[@data-role="commentContent"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'aside//li[@class="cAuthorPane_photo"]/a/img/@src'
        self.mode = 'r'

        # main function
        self.main()
