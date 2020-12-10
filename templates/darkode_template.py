# -- coding: utf-8 --
import re
import traceback

from .base_template import BaseTemplate


class DarkodeParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = kwargs.get('parser_name')
        self.thread_name_pattern = re.compile(
            r'(\d+).*html'
        )
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.date_xpath = 'td/text()'
        self.date_pattern = "%a %b %d, %Y %H:%M %p"
        self.author_xpath = 'td//span[@class="postername"]//strong/text()'
        self.title_xpath = '//td[@class="forumheader-mid"]/a/text()'
        self.post_text_xpath = 'td[@class="row1" or @class="row2"]//td[@colspan="2"]/text()'

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
            key=lambda x: (int(self.thread_name_pattern.search(x).group(1))))

        return sorted_files

    def extract_comments(self, html_response, pagination):
        comments = list()
        comment_blocks = html_response.xpath(
          '//table[@class="forumline"]/tbody/tr[not(contains(.,"Total Vote"))]'
        )
        for index, comment_block in enumerate(comment_blocks[3::3], 1):
            author_index = comment_blocks.index(comment_block) + 1
            date_index = comment_blocks.index(comment_block) + 2
            if date_index > len(comment_blocks)-1:
                break
            user = self.get_author(comment_blocks[author_index])
            comment_text = self.get_post_text(comment_blocks[author_index])
            comment_date = self.get_date(comment_blocks[date_index])
            pid = self.thread_id
            comments.append({

                '_source': {
                    'pid': pid,
                    'date': comment_date,
                    'message': comment_text.strip(),
                    'cid': str(index),
                    'author': user,
                },
            })
        return comments

    def header_data_extract(self, html_response, template):
        try:
            if html_response.xpath(
               '//b[text()="users granted special access"]'):
                return
            # ---------------extract header data ------------
            header = html_response.xpath(
                '//table[@class="forumline"]/tbody/tr[not(contains(.,"Total Vote"))]'
            )
            if not header:
                return

            thread_header = header[1].xpath(
                '//th[@class="thLeft" and contains(text(), "Author")]'
            )
            if not thread_header:
                return

            title = self.get_title(html_response)
            date = self.get_date(header[2])
            author = self.get_author(header[1])
            post_text = self.get_post_text(header[1])
            pid = self.thread_id
            return {

                '_source': {
                    'pid': pid,
                    'subject': title,
                    'date': date,
                    'author': author,
                    'message': post_text.strip(),
                }
            }
        except:
            ex = traceback.format_exc()
            raise BrokenPage(ex)

    def get_avatar(self, tag):
        pass

    def get_author(self, tag):
        author = tag.xpath(
            'td//span[contains(@class,"postername")]//strong/text()'
        )
        if not author:
            author = tag.xpath(
                'td//span[contains(@class,"postername")]//strong//text()'
            )

        author = ''.join(author)

        author = author.strip() if author else None
        return author