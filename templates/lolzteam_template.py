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

        # main function
        self.main()
