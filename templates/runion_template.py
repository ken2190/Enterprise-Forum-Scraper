# -- coding: utf-8 --
import re
import locale

from .base_template import BaseTemplate


class RUnionParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        super().__init__(*args, **kwargs)
        self.parser_name = "runion_lwplxqzvmgu43uff"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/([^/]+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[contains(@class, "blockpost row")]'
        self.header_xpath = '//div[contains(@class, "blockpost row")]'
        self.date_xpath = 'h2//span[@class="conr"]/following-sibling::a[1]/text()'
        self.date_pattern = "%Y-%m-%d %H ч."
        self.author_xpath = 'div[@class="box"]//strong/text()'
        self.title_xpath = '//title/text()'
        self.post_text_xpath = 'div[@class="box"]//div[@class="postmsg"]/descendant::text()[not(ancestor::div[@class="quotebox"])]'
        self.avatar_xpath = 'div[@class="box"]//dd[@class="postavatar"]/img/@src'
        self.comment_block_xpath = 'h2//span[@class="conr"]/text()'

        # main function
        self.main()

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(
                    x.split('/')[-1]) is not None,
                files
            )
        )
        sorted_files = sorted(
            filtered_files,
            key=lambda x: int(self.thread_name_pattern.search(
                x.split('/')[-1]).group(1)))

        return sorted_files

    def extract_comments(self, html_response, pagination):
        comments = list()
        comment_blocks = html_response.xpath(self.comments_xpath)

        comment_blocks = comment_blocks[1:]\
            if pagination == 1 else comment_blocks

        for comment_block in comment_blocks:
            user = self.get_author(comment_block)
            comment_id = self.get_comment_id(comment_block)
            if not comment_id:
                continue

            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            avatar = self.get_avatar(comment_block)
            pid = self.thread_id

            source = {
                'forum': self.parser_name,
                'pid': pid,
                'message': comment_text.strip(),
                'cid': comment_id,
                'author': user,
            }
            if comment_date:
                source.update({
                    'date': comment_date
                })
            if avatar:
                source.update({
                    'img': avatar
                })
            comments.append({
                '_source': source,
            })

        return comments
