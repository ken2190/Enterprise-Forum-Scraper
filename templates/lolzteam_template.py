import re
from .base_template import BaseTemplate


class LolzTeamParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "lolzteam.net"
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.comments_xpath = '//ol[@class="messageList"]/li[contains'\
                              '(@id, "post-")]'
        self.header_xpath = '//ol[@class="messageList"]/li[contains'\
                            '(@id, "post-")]'
        self.date_xpath = 'div//abbr[@class="DateTime"]/text()'
        self.author_xpath = './/div[@class="userText"]//a[contains(@class,'\
                            '"username")]//text()'
        self.title_xpath = '//div[@class="titleBar"]/h1/text()'
        self.post_text_xpath = 'div//div[@class="messageContent"]/'\
                               'article/blockquote/text()'
        self.avatar_xpath = 'div//div[@class="avatarHolder"]/a/span/@style'

        self.index = 1
        self.offset_hours = -3
        self.date_pattern = '%b %d, %Y at %I:%M %p'
        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date_string = date_block[0].strip() if date_block else None
        date = self.parse_date_string(date_string)
        return date