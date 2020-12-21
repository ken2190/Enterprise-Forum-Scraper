# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class SkyFraudParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "skyfraud.ru"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.header_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.date_xpath = 'table//td[1][@class="thead"]/a/following-sibling::text()'
        self.date_pattern = "%d.%m.%Y, %H:%M"
        self.title_xpath = 'table//tr[@valign="top"]/td[@class="alt2" and @id]/div[@class="smallfont"]/strong/text()'
        self.post_text_xpath = 'table//tr[@valign="top"]/td[@class="alt2" and @id]/div[@id]/descendant::text()[not(ancestor::div[@style="margin:20px; margin-top:5px; "])]'
        self.avatar_xpath = 'table//a[contains(@href, "member.php")]/img/@src'
        self.comment_block_xpath = 'table//td[2][@class="thead"]/a/strong/text()'

        # main function
        self.main()

    def get_author(self, tag):
        author = tag.xpath(
            'table//a[@class="bigusername"]/span/text()'
        )
        if not author:
            author = tag.xpath(
                'table//a[@class="bigusername"]/span/b/text()'
            )
        if not author:
            author = tag.xpath(
                'table//a[@class="bigusername"]/font/strike/text()'
            )
        if not author:
            author = tag.xpath(
                'aside/div[@class="post-username"]/span/a/strong/span/text()'
            )
        if not author:
            author = tag.xpath(
                'aside/div[@class="post-username"]/span/text()'
            )
        if not author:
            author = tag.xpath(
                'table//a[@class="bigusername"]/span//text()'
            )
        if not author:
            author = tag.xpath(
                'table//*[@class="bigusername"]/text()'
            )
        author = author[0].strip() if author else None
        return author

    def get_post_text(self, tag):
        post_text_block = tag.xpath(self.post_text_xpath)
        if not post_text_block:
            return ''
        post_text = " ".join([
            post_text.strip() for post_text in post_text_block
        ])
        protected_email = tag.xpath(self.protected_email_xpath)
        if protected_email:
            decoded_values = [
                utils.get_decoded_email(e) for e in protected_email
            ]
            for decoded_value in decoded_values:
                post_text = re.sub(
                    r'\[email.*?protected\]',
                    decoded_value,
                    post_text,
                    count=1
                )

        return post_text.strip()