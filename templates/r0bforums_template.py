# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class R0bforumsParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "r0bforums.com"
        self.thread_name_pattern = re.compile(
            r'(.*)-\d+\.html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//article[contains(@class,"post-article")]'
        self.header_xpath = '//article[contains(@class,"post-article")]'
        self.date_xpath = 'div//span[contains(@class, "post_date")]/text()'
        self.date_pattern = '%m-%d-%Y, %I:%M %p'
        self.author_xpath = './/div[contains(@class,"post-username")]//text()'
        self.title_xpath = '//div[@class="thread-header"]/h1/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = './/div[contains(@class,"right postbit-number")]//text()'

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
        author = tag.xpath(self.author_xpath)
        author = ''.join(author)
        if not author:
            author = tag.xpath(
                'div//div[contains(@class,"post-username")]/a/span/text()'
            )

        author = author.strip() if author else None
        return author

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        comment_block = ''.join(comment_block)
        if comment_block:
            comment_id = comment_block.strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')
