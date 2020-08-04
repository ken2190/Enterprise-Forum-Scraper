# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class ProLogicParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "prologic.su"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[contains(@id, "post_id_")]/div[@class="post_wrap"]'
        self.header_xpath = '//div[contains(@id, "post_id_")]/div[@class="post_wrap"]'
        self.date_xpath = 'h3/div[@class="post_date"]/abbr/@title'
        self.date_pattern = "%Y-%m-%dT%H:%M:%S"
        self.author_xpath = 'h3//span[@class="author vcard"]/a/span/text()'
        self.title_xpath = '//div[@class="maintitle clear clearfix"]/span/text()'
        self.post_text_xpath = 'div[@class="post_body"]/div[@itemprop="commentText"]/descendant::text()[not(ancestor::div[@class="blockquote"]) and not(ancestor::p[@class="citation"])]'
        self.avatar_xpath = 'div//li[@class="avatar"]/a/img/@src'
        self.comment_block_xpath = 'h3//a[@itemprop="replyToUrl"]/text()'

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
            key=lambda x: (int(self.thread_name_pattern.search(x).group(1)),
                           int(self.pagination_pattern.search(x).group(1))))

        return sorted_files

    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if not author:
            author = tag.xpath(
                'h3//span[@class="author vcard"]/descendant::text()'
            )

        author = ''.join(author).strip() if author else None
        return author
