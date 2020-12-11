# -- coding: utf-8 --
import re
# import locale
import datetime
import dateparser

from .base_template import BaseTemplate


class CardingTeamParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "cardingteam.cc"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@class="newposts"]'
        self.header_xpath = '//div[@class="newposts"]'
        self.date_xpath = 'div//span[@class="post_date2"]/descendant::text()'
        self.author_xpath = 'div//strong/span[@class="largetext"]/descendant::text()'
        self.title_xpath = '//td[@class="thead"]/div/strong/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.comment_block_xpath = 'div//div[@class="float_right"]/strong/a/text()'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'

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

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = date_block[0].strip() if date_block else ""
        try:
            date = str(datetime.datetime.now().year) + ' ' + date
            pattern = "%Y %A %d | %I:%M:%p"
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except Exception:
            date = ' '.join(date_block)
            try:
                date = dateparser.parse(date).timestamp()
                return str(date)
            except:
                pass

        return ""
