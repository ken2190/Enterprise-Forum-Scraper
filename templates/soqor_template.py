# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class SoqorParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "forums.soqor.net"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//ul[contains(@class,"conversation-list")]/li[contains(@class,"b-post")]'
        self.header_xpath = '//ul[contains(@class,"conversation-list")]/li[contains(@class,"b-post")]'
        self.date_xpath = './/div[contains(@class,"post__timestamp")]/time/@datetime'
        self.author_xpath = './/a[contains(@class,"b-avatar")]/img/@title'
        self.title_xpath = '//h2[contains(@class,"b-post__title")]/text()'
        self.post_text_xpath = './/div[contains(@class,"js-post__content-text")]//text()[not(ancestor::div[contains(@class,"bbcode_container")])]'
        self.avatar_xpath = './/a[contains(@class,"b-avatar")]/img/@src'
        self.comment_block_xpath = './/a[contains(@class,"post__count")]/text()'

        # main function
        self.main()

    def get_avatar(self, tag):
        avatar_block = tag.xpath(self.avatar_xpath)
        if not avatar_block:
            return ""

        if "image.php" in avatar_block[0]:
            avatar_name_pattern = re.compile(r'u=(\d+)')
            name_match = avatar_name_pattern.findall(avatar_block[0])
            if name_match:
                name = f'{name_match[0]}.jpg'
                return name

        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""

        return name_match[0]
