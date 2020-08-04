# -- coding: utf-8 --
import re
import utils
import dateutil.parser as dparser

from .base_template import BaseTemplate


class RaidForumsParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "raidforums.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/([^/]+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="posts"]/div[contains(@class,"post")]'
        self.header_xpath = '//div[@id="posts"]/div[contains(@class,"post")]'
        self.date_xpath = 'div//span[@class="post_date"]/text()'
        self.author_xpath = 'div//div[@class="post__user-profile largetext"]//span/text()'
        self.title_xpath = '//span[@class="thread-info__name rounded"]/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]//descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'div//a[@class="post__user-avatar"]/img/@src'
        self.comment_block_xpath = 'div//div[@class="post_head"]//a/text()'

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
                'forum': "raidforums.com",
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

    def get_date(self, tag):
        date = tag.xpath(self.date_xpath)
        date = date[-1].strip() if date else None

        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except:
            return ""

    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if not author:
            author = tag.xpath(
                'div//div[@class="post__user-profile largetext"]/text()'
            )

        author = author[0].strip() if author else None
        return author

    def get_post_text(self, tag):
        post_text = tag.xpath(self.post_text_xpath)
        protected_email = tag.xpath(
            'div//div[@class="post_body scaleimages"]/'
            'descendant::*[@class="__cf_email__"]/@data-cfemail'
        )
        post_text = "\n".join(
            [text.strip() for text in post_text]
        ) if post_text else ""

        if protected_email:
            decoded_values = [utils.get_decoded_email(e) for e in protected_email]
            for decoded_value in decoded_values:
                post_text = re.sub(
                    r'\[email.*?protected\]',
                    decoded_value,
                    post_text,
                    count=1
                )

        return post_text
