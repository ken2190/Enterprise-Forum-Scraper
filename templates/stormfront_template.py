# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


class StormFrontParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "stormfront.org"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(
            r"u=(\d+)",
            re.IGNORECASE
        )
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.mode = 'r'
        self.comments_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.header_xpath = '//div[@id="posts"]//div[@class="page"]/div/div[@id]'
        self.date_xpath = './/td[@class="thead"][1]/a[contains(@name,"post")]/following-sibling::text()[1]'
        self.author_xpath = './/a[@class="bigusername"]/descendant::text()'
        self.title_xpath = '//span[@itemprop="title"]/text()'
        self.post_text_xpath = './/div[contains(@id, "post_message")]/descendant::text()[not(ancestor::div[@style="margin:20px; margin-top:5px; "])]'
        self.avatar_xpath = '//a[contains(@href, "member.php?") and img/@src]/@href'
        self.comment_block_xpath = './/a[contains(@id,"postcount")]/@name'

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
