# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class SecurityLabParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "securitylab.ru"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//table[contains(@class,"forum-post-table")]'
        self.header_xpath = '//table[contains(@class,"forum-post-table")]'
        self.date_xpath = './/div[contains(@class,"forum-post-date")]/span/text()'
        self.author_xpath = './/div[contains(@class,"forum-user-name")]/*/text()'
        self.title_xpath = '//div[contains(@class,"forum-header-title")]//span//text()'
        self.post_text_xpath = './/div[contains(@class,"forum-post-text")]//text()[not(ancestor::table[@class="forum-quote"])]'
        self.avatar_xpath = './/img[contains(@class,"avatar")]/@src'
        self.comment_block_xpath = './/div[contains(@class,"forum-post-number")]//a/text()'

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

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = ''.join(title)
        title = title.strip() if title else None

        return title

    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if author:
            author = ''.join(author).strip()
            return author
        else:
            return 'Guest'