# -- coding: utf-8 --
import re
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class BitCoinTalkParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "bitcointalk.com"
        # self.thread_name_pattern = re.compile(
        #     r'(\d+).*html$'
        # )
        # self.pagination_pattern = re.compile(
        #     r'.*-(\d+)\.html$'
        # )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//tr[@class]//td[contains(@class,"windowbg") and not(@valign)]'
        self.header_xpath = '//tr[@class]//td[contains(@class,"windowbg") and not(@valign)]'
        self.date_xpath = 'table//td[@valign="middle"]/div[@class="smalltext"]/text()'
        self.date_pattern = '%B %d, %Y, %I:%M:%S %p'
        self.author_xpath = 'table//td[@class="poster_info"]/b/a/text()'
        self.title_xpath = 'table//div[@class="subject"]/a/text()'
        self.post_text_xpath =  'table//div[@class="post"]/text()'
        self.comment_block_xpath = 'table//td[@class="td_buttons"]/div/a/text()'
        self.avatar_xpath = '//img[@class="avatar"]/@src'

        # main function
        self.main()

    # def get_filtered_files(self, files):
    #     filtered_files = list(
    #         filter(
    #             lambda x: self.thread_name_pattern.search(x) is not None,
    #             files
    #         )
    #     )
    #     sorted_files = sorted(
    #         filtered_files,
    #         key=lambda x: (self.thread_name_pattern.search(x).group(1),
    #                        self.pagination_pattern.search(x).group(1)))

    #     return sorted_files

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        if not date_block:
            date_block = tag.xpath(
                'table//td[@valign="middle"]'
                '/div[@class="smalltext"]/span[@class="edited"]/text()'
            )

        date = date_block[0].strip() if date_block else ""
        if date.startswith('at '):
            date = datetime.datetime.today().strftime('%B %d, %Y, ') + date.split('at ')[-1]

        try:
            date = datetime.datetime.strptime(date, self.date_pattern).timestamp()
            return str(date)
        except:
            try:
                date = dparser.parse(date).timestamp()
                return str(date)
            except:
                pass

        return ""

    def get_comment_id(self, tag):
        reply_block = tag.xpath(
            'table//td[@class="td_buttons"]'
            '/div/a/img[@class="reply_button"]'
        )
        if reply_block:
            return

        comment_block = tag.xpath(self.comment_block_xpath)
        if comment_block:
            commentID = comment_block[0].split('#')[-1].replace(',', '')
            return commentID.replace(',', '')

        return ""
