# -- coding: utf-8 --
import re
import dateutil.parser as dparser

from .base_template import BaseTemplate


class LCPCCParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "lcp.cc"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/([^/]+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//table[@class="posthead"]'
        self.header_xpath ='//table[@class="posthead"]'
        self.date_xpath = 'tr//td[@style="text-align:right;"]//text()'
        self.author_xpath = 'tr//td[@style="text-align:right;"]/preceding-sibling::td[1]/text()'
        self.title_xpath = '//hr/preceding-sibling::b[1]/text()'
        self.post_text_xpath = 'following-sibling::text()'
        self.avatar_xpath = 'div//a[@class="post__user-avatar"]/img/@src'
        self.comment_block_xpath = 'tr//td[@style="text-align:right;"]/preceding-sibling::td[1]/text()'

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

    def get_date(self, tag):
        date = tag.xpath(self.date_xpath)
        date = ''.join(date)
        if not date:
            return ''

        pattern = re.compile(r'\s*on\s*(.*)')
        match = pattern.findall(date.strip())
        if not match:
            return

        try:
            date = dparser.parse(match[0]).timestamp()
            return str(date)
        except:
            return ""

    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if not author:
            return ''

        author = ' '.join(author)
        pattern = re.compile(r'(\w+),')
        match = pattern.findall(author.strip())
        if not match:
            return

        return re.sub(r'\[.*?\]', '', match[0])

    def get_comment_id(self, tag):
        comment_block = tag.xpath(self.comment_block_xpath)
        if not comment_block:
            return ''

        pattern = re.compile(r'\d+')
        match = pattern.findall(comment_block[0])
        if not match:
            return

        return match[0]
