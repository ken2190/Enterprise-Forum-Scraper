import re
from .base_template import BaseTemplate


class CCrackingOrgParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "c-cracking.org"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.index = 1
        self.comments_xpath = '//article[contains(@id, "elComment_")]'
        self.header_xpath = '//article[contains(@id, "elComment_")]'
        self.date_xpath = './/time/@datetime'
        self.author_xpath = './/aside//a[@class="ipsType_break"]//text()|aside//strong[@itemprop="name"]//text()'
        self.title_xpath = '//span[@class="ipsType_break ipsContained"]/span/text()'
        self.post_text_xpath = './/div//div[@data-role="commentContent"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = './/aside//div[contains(@class, "cAuthorPane_")]' \
                            '//a[contains(@class, "ipsUserPhoto")]/img/@src'
        self.mode = 'r'
        self.date_pattern = '%Y-%m-%dT%H:%M:%SZ'

        # main function
        self.main()
