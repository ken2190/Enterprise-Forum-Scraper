import re
from .base_template import BaseTemplate


class XakerParser(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "xaker.name"
        self.avatar_name_pattern = re.compile(r".*/(\d+\.\w+)")
        self.mode = 'r'
        self.comments_xpath = '//ol[@class="messageList"]/li[contains(@class,"message")]'
        self.header_xpath = '//ol[@class="messageList"]/li[contains(@class,"message")]'
        self.date_xpath = './/span[@class="DateTime"]/@title'
        self.author_xpath = './/div[@class="userText"]/a[contains(@class,"username")]/text()|'\
                            './/div[@class="userText"]/a[contains(@class,"username")]/span/text()'
        self.post_text_xpath = './/div[contains(@class,"messageContent")]//article/blockquote/descendant::text()[not(ancestor::div[contains(@class,"bbCodeQuote")])]'
        self.avatar_xpath = './/div[contains(@class,"avatarHolder")]//img/@src'
        self.title_xpath = '//h1/text()'
        self.index = 1

        # main function
        self.main()
