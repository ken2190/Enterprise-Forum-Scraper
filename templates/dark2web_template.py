# -- coding: utf-8 --
import re
import locale

from .base_template import BaseTemplate


class Dark2WebParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        super().__init__(*args, **kwargs)
        self.parser_name = "dark2web.ru"
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.comments_xpath = '//div[@class="message-inner"]'
        self.header_xpath = '//div[@class="message-inner"]'
        self.date_xpath = 'div//div[@class="message-attribution-main"]/a/time/@title'
        self.date_pattern = "%d.%m.%Y в %H:%M"
        self.title_xpath = '//h1[@class="p-title-value"]//text()'
        self.post_text_xpath = 'div//div[@class="bbWrapper"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'div//div[@class="message-avatar-wrapper"]/a/img/@src'
        self.comment_block_xpath = 'div//header[@class="message-attribution message-attribution--split"]//a/text()'
        self.author_xpath = './/div[contains(@class, "nadavoi")]//a[contains(@class, "username")]//text()'

        # main function
        self.main()
