# -- coding: utf-8 --
from .base_template import BaseTemplate


class HeliumParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "helium"
        self.mode = 'r'
        self.index = 1
        self.comments_xpath = "//div[@id='a9']"
        self.header_xpath = "//div[@id='a9']"
        self.author_xpath = ".//div[@class='panel-title']//a/text()"
        self.title_xpath = "//*[@class='text-truncated']/text()"
        self.post_text_xpath = ".//div[@class='content_body']//text()"

        # main function
        self.main()

    def get_date(self, tag):
        """
        Return empty value since this site doesn't have any timestamp anywhere.
        """
        return ''

    def get_avatar(self, tag):
        """
        Return empty value since this site doesn't have any avatar for every posts.
        """
        return ''
