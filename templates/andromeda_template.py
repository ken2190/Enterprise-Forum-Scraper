# -- coding: utf-8 --
import re
import traceback
import utils
import datetime
from lxml.html import fromstring

from .base_template import BaseTemplate, BrokenPage


class AndromedaParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "andromeda market"
        self.thread_name_pattern = re.compile(
            r'index.php.*topic[=,](\d+)'
        )
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.header_xpath = '//div[@class="windowbg"]'
        self.comments_xpath = '//div[contains(@class, "windowbg")]'
        self.date_xpath = 'div[@class="date_post"]/div/text()'
        self.date_pattern = '%B %d, %Y, %I:%M:%S  %p'
        self.author_xpath = 'div[@class="post_wrapper"]/div[@class="poster"]/h4/a/text()'
        self.title_xpath = 'div[@class="post_wrapper"]/div[@class="postarea"]//h5/a/text()'
        self.comment_block_xpath = 'div[@class="date_post"]/span/text()'

        # main function
        self.main()

    def get_pid(self):
        pid_pattern = re.compile(r'topic[=,](\d+)')
        pid = pid_pattern.findall(self.thread_id)
        pid = pid[0] if pid else self.thread_id

        return pid

    def get_html_response(self, file):
        with open(file, 'rb') as f:
            content = str(f.read())
            splitter = 'Content-Type: text/html; charset=UTF-8'
            content = content.split(splitter)[-1]
            content = content.replace('\\r', '')\
                             .replace('\\n', '')\
                             .replace('\\t', '')\
                             .strip()
            html_response = fromstring(content)
            return html_response

    def main(self):
        comments = []
        for index, template in enumerate(self.files):
            print(template)
            try:
                # read html file
                if template.endswith('.txt'):
                    html_response = self.get_html_response(template)
                else:
                    html_response = utils.get_html_response(template)
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern.findall(file_name_only)
                if not match:
                    continue

                self.thread_id = match[0]
                pid = self.get_pid()
                final = utils.is_file_final(
                    self.thread_id, self.thread_name_pattern, self.files, index
                )

                output_file = None
                if self.thread_id not in self.distinct_files and\
                   not output_file:

                    # header data extract
                    data = self.header_data_extract(html_response, template)
                    if not data:
                        comments.extend(self.extract_comments(html_response))
                        continue

                    self.distinct_files.add(self.thread_id)

                    # write file
                    output_file = '{}/{}.json'.format(
                        str(self.output_folder),
                        pid
                    )
                    file_pointer = open(output_file, 'w', encoding='utf-8')
                    utils.write_json(file_pointer, data)
                # extract comments
                comments.extend(self.extract_comments(html_response))

                if final:
                    utils.write_comments(file_pointer, comments, output_file)
                    comments = []
            except BrokenPage as ex:
                utils.handle_error(
                    pid,
                    self.error_folder,
                    ex
                )
            except:
                traceback.print_exc()
                continue

    def get_post_text(self, tag):
        post_text = tag.xpath(
            'div[@class="post_wrapper"]/'
            'div[@class="postarea"]'
            '//div[@class="post"]/'
            '/div[@class="inner"]/text()'
        )
        if not post_text:
            post_text = tag.xpath(
                'div[@class="post_wrapper"]/'
                'div[@class="postarea"]'
                '//div[@class="post"]/'
                '/div[@class="inner"]'
                '/code[@class="bbc_code"]/text()'
            )

        post_text = "\n".join(
            [text.strip() for text in post_text]
        ) if post_text else ""

        return post_text

    def get_comment_id(self, tag):
        commentID = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        if comment_block:
            comment_pattern = re.compile(r'Reply #(\d+)')
            match = comment_pattern.findall(comment_block[0])
            commentID = match[0] if match else ""

        return commentID.replace(',', '')
