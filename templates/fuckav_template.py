# -- coding: utf-8 --
import re
import dateparser as dparser

from .base_template import BaseTemplate


class FuckavParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "fuckav.ru"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'u=(\d+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.mode = 'r'
        self.comments_xpath = '//table[contains(@id, "post")]'
        self.header_xpath = '//table[contains(@id, "post")]'
        self.date_xpath = 'tr//td[@class="alt1" and @align="right"]/div/text()'
        self.date_pattern = '%d-%m-%Y, %H:%M'
        self.title_xpath = '//td[@class="navbar"]/a/following-sibling::strong[1]/text()'
        self.post_text_xpath = 'tr//div[contains(@id, "post_message_")]/descendant::text()[not(ancestor::div[@style="margin:20px; margin-top:5px; "])]'
        self.avatar_xpath = 'tr//a[contains(@href, "member.php")]/img/@src'
        self.avatar_ext = 'jpg'
        self.comment_block_xpath = 'tr//td[@class="alt1" and @align="right"]/a/strong/text()'

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
            pid = self.thread_id
            avatar = self.get_avatar(comment_block)

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
        author = tag.xpath(
            'tr//a[@class="bigusername"]/text()'
        )
        if not author:
            author = tag.xpath(
                'tr//a[@class="bigusername"]/strike/text()'
            )

        if not author:
            author = tag.xpath(
                'tr//a[@class="bigusername"]/i/text()'
            )

        if not author:
            author = tag.xpath(
                'tr//a[@class="bigusername"]/s/text()'
            )

        if not author:
            author = tag.xpath(
                'tr//a[@class="bigusername"]/span/text()'
            )

        if not author:
            author = tag.xpath(
                'tr//a[@class="bigusername"]/span/i/text()'
            )

        if not author:
            author = tag.xpath(
                'tr//a[@class="bigusername"]/font/text()'
            )

        author = author[0].strip() if author else None
        return author

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)

        date = ""
        if date_block:
            date = [d.strip() for d in date_block if d.strip()][0]

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
        comment_block = tag.xpath(self.comment_block_xpath)
        if not comment_block:
            return ''

        pattern = re.compile(r'\d+')
        match = pattern.findall(comment_block[0])
        if not match:
            return

        return match[0]
