# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class MazaParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "maza.la"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'u=(\d+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.mode = 'r'
        self.comments_xpath = '//ol[@id="posts"]/li'
        self.header_xpath = '//ol[@id="posts"]/li'
        self.date_xpath =  './/span[@class="time"]/preceding-sibling::text()'
        self.author_xpath = './/div[@class="username_container"]//a[contains(@href, "member.php")]/descendant::text()'
        self.title_xpath = '//span[@class="threadtitle"]/a/text()'
        self.post_text_xpath = './/blockquote[contains(@class,"postcontent restore")]/descendant::text()[not(ancestor::div[@class="bbcode_container"])]'
        self.avatar_xpath = './/a[@class="postuseravatar"]/@href'
        self.avatar_ext = 'jpg'
        self.comment_block_xpath = './/a[@class="postcounter"]/text()'

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
            key=lambda x: (
                int(self.thread_name_pattern.search(x).group(1)),
                int(self.pagination_pattern.search(x).group(1))
            ))

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

    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if not author:
            author = tag.xpath(
                './/div[@class="username_container"]'
                '/span[contains(@class,"username")]'
                '/descendant::text()'
            )

        return author[0].strip() if author else None

    def get_comment_id(self, tag):
        comment_block = tag.xpath(self.comment_block_xpath)
        if not comment_block:
            return ''

        pattern = re.compile(r'\d+')
        match = pattern.findall(comment_block[0])
        if not match:
            return

        return match[0]
