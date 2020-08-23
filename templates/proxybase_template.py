# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class ProxyBaseParser(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "http://proxy-base.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(
            r".dateline=(\d+).",
            re.IGNORECASE
        )

        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.header_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.comment_block_xpath = 'table//td[2][@class="thead"]/a/strong//text()'
        self.post_text_xpath = 'table//tr[@valign="top"]/td[@class="alt1" and @id]/div[@id]/descendant::text()[not(ancestor::div[@style="margin:20px; margin-top:5px; "])]'

        self.date_xpath = 'table//td[1][@class="thead"]/a/following-sibling::text()'

        self.date_pattern = "%m/%d/%Y at %H:%M"
        self.title_xpath = 'table//tr[@valign="top"]/td[@class="alt1" and @id]/div[@class="smallfont"]/strong//text()'

        self.main()

    def get_author(self, tag):
        author = tag.xpath(
            'table//a[@class="bigusername"]//text()'
        )
        if not author:
            author = tag.xpath(
                'table//div[contains(@id, "postmenu_")]/text()'
            )
        if not author:
            author = tag.xpath(
                'table//a[@class="bigusername"]/span/b/text()'
            )
        if not author:
            author = tag.xpath(
                'table//a[@class="bigusername"]/font/strike/text()'
            )

        author = author[0].strip() if author else None

        return author

    def get_avatar(self, tag):
        avatar_block = tag.xpath(
            './/td[1]//a[contains(@rel, "nofollow") and img]/img/@src'
        )
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

        return f'{name_match[0]}.jpg'

    # def get_comment_id(self, tag):
    #     comment_id = ""
    #     comment_block = tag.xpath(self.comment_block_xpath)
    #     if comment_block:
    #         comment_id = comment_block[-1].strip().split('#')[-1]
    #     return comment_id.replace(',', '').replace('.', '')
