# -- coding: utf-8 --
import re
import utils

from .base_template import BaseTemplate


class MafiaUgParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = 'mafia.ug'
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//article[contains(@class,"cPost ipsBox")]'
        self.header_xpath = '//article[contains(@class,"cPost ipsBox")]'
        self.date_xpath = 'div//time/@datetime'
        self.author_xpath = 'aside//div[@class="name"]//strong/a//text()'
        self.title_xpath = '//h1[contains(@class, "ipsType_pageTitle")]//text()'
        self.avatar_xpath = '//div[contains(@class, "cAuthorPane_photo")]/a/img/@src'
        self.avatar_ext = ''
        self.comment_block_xpath = 'div//span[@data-role="reactCountText"]/text()'
        # main function
        self.main()

    def get_post_text(self, tag):
        post_text_block = tag.xpath(
            'div//div[@data-role="commentContent"]'
            '/descendant::text()[not(ancestor::blockquote)]'
        )
        protected_email = tag.xpath(
            'div//div[@class="post_body scaleimages"]/'
            'descendant::*[@class="__cf_email__"]/@data-cfemail'
        )
        post_text = "".join([
            post_text.strip() for post_text in post_text_block
        ])
        if protected_email:
            decoded_values = [utils.get_decoded_email(e) for e in protected_email]
            for decoded_value in decoded_values:
                post_text = re.sub(
                    r'\[email.*?protected\]',
                    decoded_value,
                    post_text,
                    count=1
                )
        return post_text.strip().encode('latin1', errors='ignore').decode('utf8', errors='ignore')
    
    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = "".join([t.strip() for t in title if t.strip()])

        return title.strip().encode('latin1', errors='ignore').decode('utf8', errors='ignore')

    def get_author(self, tag):
        author = tag.xpath(
            'aside//a[@class="ipsType_break"]/span/span/text()'
        )
        if not author:
            author = tag.xpath(
                'aside//a[@class="ipsType_break"]/span/text()'
            )
        if not author:
            author = tag.xpath(
                'aside//a[@class="ipsType_break"]/text()'
            )
        if not author:
            author = tag.xpath(
                'aside//div[contains(@class, "lkComment_author")]/descendant::text()'
            )
        if not author:
            author = tag.xpath(
                './/h3[contains(@class, "cAuthorPane_author")]/strong/text()'
            )
        author = ' '.join(author).strip() if author else None

        return author
