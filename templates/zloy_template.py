# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class ZloyParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "zloy.bz"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.mode = 'r'
        self.comments_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.header_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.date_xpath = 'table//td[1][@class="thead"]/a/following-sibling::text()'
        self.date_pattern = "%d.%m.%Y, %H:%M"
        self.title_xpath = 'table//tr[@valign="top"]/td[@class="alt1" and @id]/div[@class="smallfont"]/strong/text()'
        self.post_text_xpath = 'table//tr[@valign="top"]/td[@class="alt1" and @id]/div[@id]/descendant::text()[not(ancestor::div[@style="margin:20px; margin-top:5px; "])]'
        self.avatar_xpath = 'table//a[contains(@href, "member.php")]/img/@src'
        self.comment_block_xpath = 'table//td[2][@class="thead"]/a/strong/text()'

        # main function
        self.main()

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(x) is not None,
                files
            )
        )
        sorted_files = sorted(
            filtered_files,
            key=lambda x: (self.thread_name_pattern.search(x).group(1),
                           self.pagination_pattern.search(x).group(1)))

        return sorted_files

    def get_author(self, tag):
        author = tag.xpath(
            'table//a[@class="bigusername"]//text()'
        )
        if not author:
            author = tag.xpath(
                'table//div[contains(@id, "postmenu_")]//text()'
            )
        if not author:
            author = tag.xpath(
                'table//a[@class="bigusername"]/span/b//text()'
            )
        if not author:
            author = tag.xpath(
                'table//a[@class="bigusername"]/font/strike//text()'
            )

        author = author[0].strip() if author else None
        return author

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
