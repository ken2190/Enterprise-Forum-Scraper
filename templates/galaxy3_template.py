# -- coding: utf-8 --
import re
import traceback

from .base_template import BaseTemplate, BrokenPage


class Galaxy3Parser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = kwargs.get('parser_name')
        self.thread_name_pattern = re.compile(
            r'(\d+).*html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@class="elgg-main elgg-body"]/ul[@class="elgg-list elgg-list-entity"]/li'
        self.header_xpath = '//div[@class="elgg-main elgg-body"]/ul[@class="elgg-list elgg-list-entity"]/li'
        self.date_xpath = 'div//div[@class="elgg-listing-summary-subtitle elgg-subtext"]/time/@title'
        self.date_pattern = "%d %B %Y @ %H:%M%p"
        self.title_xpath = '//h1[@class="main-title"]/a/text()'
        self.post_text_xpath = 'div//div[@class="elgg-listing-summary-content elgg-content"]'
        self.avatar_ext = 'div[@class="elgg-image-block clearfix thewire-post"]//img/@src'

        # main function
        self.main()

    def extract_comments(self, html_response, pagination):
        comments = list()
        comment_blocks = html_response.xpath(self.comments_xpath)
        comment_blocks.reverse()

        for index, comment_block in enumerate(comment_blocks[1:], 1):
            user = self.get_author(comment_block)
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            avatar = self.get_avatar(comment_block)
            pid = self.thread_id

            source = {
                'forum': self.parser_name,
                'pid': pid,
                'message': comment_text.strip(),
                'cid': str(index),
                'author': user,
                'img': avatar,
            }
            if comment_date:
                source.update({
                    'date': comment_date
                })
            comments.append({
                '_source': source,
            })

        return comments

    def header_data_extract(self, html_response, template):
        try:

            # ---------------extract header data ------------
            header = html_response.xpath(self.header_xpath)
            if not header:
                return

            title = self.get_title(header[-1])
            date = self.get_date(header[-1])
            author = self.get_author(header[-1])
            post_text = self.get_post_text(header[-1])
            avatar = self.get_avatar(header[-1])
            pid = self.thread_id

            source = {
                'forum': self.parser_name,
                'pid': pid,
                'subject': title,
                'date': date,
                'author': author,
                'img': avatar,
                'message': post_text.strip(),
            }
            if date:
                source.update({
                   'date': date
                })
            return {
                '_source': source
            }
        except:
            ex = traceback.format_exc()
            raise BrokenPage(ex)

    def get_author(self, tag):
        author = tag.xpath(
            'div//div[@class="elgg-listing-summary-subtitle elgg-subtext"]/'
            'a/text()'
        )
        if not author:
            author = tag.xpath(
                'tr//div[contains(@id, "postmenu_")]/text()'
            )

        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        return "Thread"
        title = tag.xpath(self.title_xpath)
        title = title[-1].strip() if title else None

        return title

    def get_post_text(self, tag):
        post_text_block = tag.xpath(self.post_text_xpath)
        post_text = "\n".join([
            post_text.xpath('string()') for post_text in post_text_block
        ])

        return post_text.strip()
