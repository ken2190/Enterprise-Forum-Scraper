# -- coding: utf-8 --
import re
import locale

from .base_template import BaseTemplate


class Dark2WebParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        super().__init__(*args, **kwargs)
        self.parser_name = "dark2web.ru"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@class="message-inner"]'
        self.header_xpath = '//div[@class="message-inner"]'
        self.date_xpath = 'div//div[@class="message-attribution-main"]/a/time/@title'
        self.date_pattern = "%d.%m.%Y в %H:%M"
        self.title_xpath = '//h1[@class="p-title-value"]/text()'
        self.post_text_xpath = 'div//div[@class="bbWrapper"]/descendant::text()[not(ancestor::div[contains(@class, "bbCodeBlock bbCodeBlock--expandable bbCodeBlock--quote")])]'
        self.avatar_xpath = 'div//div[@class="message-avatar-wrapper"]/a/img/@src'
        self.comment_block_xpath = 'div//header[@class="message-attribution message-attribution--split"]//a/text()'
        self.author_xpath = '//div[contains(@class, "nadavoi")]//span[contains(@class, "username--style")]/text()'

        # main function
        self.main()

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        if comment_block:
            comment_id = comment_block[-1].split('#')[-1]

        return comment_id.replace(',', '').strip()
