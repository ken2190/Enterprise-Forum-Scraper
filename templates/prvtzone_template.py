# -- coding: utf-8 --
import re
import traceback
import datetime

from .base_template import BaseTemplate, BrokenPage


class PrvtZoneParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "prvtzone.ws"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//ol[@class="messageList"]/li'
        self.header_xpath = '//ol[@class="messageList"]/li'
        self.date_xpath = 'div//a[@class="datePermalink"]/span/@title'
        self.author_xpath = '@data-author'
        self.title_xpath = '//div[@class="titleBar"]/h1/text()'
        self.post_text_xpath = 'div//div[@class="messageContent"]/article/blockquote/descendant::text()[not(ancestor::div[@class="bbCodeBlock bbCodeQuote"])]'
        self.avatar_xpath = 'div//div[@class="avatarHolder"]/a/img/@src'
        self.comment_block_xpath = 'div//div[@class="publicControls"]/a/text()'

        # main function
        self.main()

    def header_data_extract(self, html_response, template):
        try:

            # ---------------extract header data ------------
            header = html_response.xpath(
                '//ol[@class="messageList messageArticle"]/li'
            )
            if not header:
                header = html_response.xpath(self.header_xpath)
            if not header:
                return

            title = self.get_title(html_response)
            date = self.get_date(header[0])
            author = self.get_author(header[0])
            post_text = self.get_post_text(header[0])
            avatar = self.get_avatar(header[0])
            pid = self.thread_id

            source = {
                'forum': self.parser_name,
                'pid': pid,
                'subject': title,
                'author': author,
                'message': post_text.strip(),
            }
            if date:
                source.update({
                   'date': date
                })
            if avatar:
                source.update({
                    'img': avatar
                })
            return {
                '_source': source
            }
        except:
            ex = traceback.format_exc()
            raise BrokenPage(ex)

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        if not date_block:
            date_block = tag.xpath(
                'div//a[@class="datePermalink"]'
                '/abbr/text()'
            )

        date = date_block[0].strip() if date_block else ""
        try:
            pattern = "%b %d, %Y at %I:%M %p"
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except:
            return ""
