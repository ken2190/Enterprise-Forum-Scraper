# -- coding: utf-8 --
import re
#import locale
import datetime
import dateparser

from .base_template import BaseTemplate


class CarderMeParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "carder.me"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comment_pattern = re.compile(r'(\<\!--.*?--\!?\>)', re.DOTALL)
        self.encoding = 'ISO-8859-1'
        self.comments_xpath = '//div[@id="posts"]//div[@id and @style]'
        self.header_xpath = '//div[@id="posts"]//div[@id and @style]'
        self.date_xpath = 'div[@class="tcat"]/text()'
        self.date_pattern = "%m-%d-%Y, %I:%M %p"
        self.author_xpath = 'table//a[@class="bigusername"]/span/descendant::text()|'\
            'table//div[contains(@id, "postmenu_")]/text()'
        self.title_xpath = '//title/text()'
        self.post_text_xpath = 'table//td[@class="alt1 rightside"]/div[@id]'
        self.comment_block_xpath = 'div[@class="tcat"]/span/a/strong/text()'
        self.avatar_xpath = 'table//td[@class="alt2 leftside"]/div/a/img/@src'

        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = date_block[-1].strip() if date_block else ""
        try:
            date = datetime.datetime.strptime(date, self.date_pattern).timestamp()
            return str(date)
        except:
            try:
                date = dateparser.parse(date).timestamp()
                return str(date)
            except:
                pass

        return ""

    def get_post_text(self, tag):
        post_text_block = tag.xpath(self.post_text_xpath)
        post_text = "\n".join([
            post_text.xpath('string()') for post_text in post_text_block
        ])

        return post_text.strip().replace('\\n', ' ').replace('\\t', ' ')
