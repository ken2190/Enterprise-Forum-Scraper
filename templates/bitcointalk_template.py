# -- coding: utf-8 --
import os
import re
from collections import OrderedDict
import traceback
import json
import utils
import datetime
from lxml.html import fromstring


class BrokenPage(Exception):
    pass


class BitCoinTalkParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = parser_name
        self.output_folder = output_folder
        self.thread_name_pattern = re.compile(
            r'(\d+).*html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(files)
        self.folder_path = folder_path
        self.data_dic = OrderedDict()
        self.distinct_files = set()
        self.error_folder = "{}/Errors".format(output_folder)
        self.thread_id = None
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
            key=lambda x: int(self.thread_name_pattern.search(x).group(1)))

        return sorted_files

    def main(self):
        comments = []
        output_file = None
        for index, template in enumerate(self.files):
            print(template)
            try:
                html_response = utils.get_html_response(template)
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern.findall(file_name_only)
                if not match:
                    continue
                pid = self.thread_id = match[0]
                final = utils.is_file_final(
                    self.thread_id, self.thread_name_pattern, self.files, index
                )
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
                    output_file = None
            except BrokenPage as ex:
                utils.handle_error(
                    pid,
                    self.error_folder,
                    ex
                )
            except:
                traceback.print_exc()
                continue

    def extract_comments(self, html_response):
        comments = list()
        comment_blocks = html_response.xpath(
          '//td[contains(@class,"windowbg") and not(@valign)]'
        )
        for comment_block in comment_blocks:

            user = self.get_author(comment_block)
            commentID = self.get_comment_id(comment_block)
            if not commentID or commentID == "1":
                continue
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            pid = self.thread_id
            avatar = self.get_avatar(comment_block)
            source = {
                'forum': self.parser_name,
                'pid': pid,
                'message': comment_text.strip(),
                'cid': commentID,
                'author': user,
                'img': avatar,
            }
            if comment_date:
                source.update({
                    'd': comment_date
                })
            comments.append({
                
                '_source': source
            })
        return comments

    def header_data_extract(self, html_response, template):
        try:

            # ---------------extract header data ------------
            header = html_response.xpath(
                '//td[contains(@class,"windowbg") and not(@valign)]'
            )
            if not header:
                return
            if not self.get_comment_id(header[0]) == "1":
                return
            title = self.get_title(header[0])
            date = self.get_date(header[0])
            author = self.get_author(header[0])
            post_text = self.get_post_text(header[0])
            pid = self.thread_id
            avatar = self.get_avatar(header[0])
            source = {
                'forum': self.parser_name,
                'pid': pid,
                's': title,
                'a': author,
                'm': post_text.strip(),
                'img': avatar,
            }
            if date:
                source.update({
                   'd': date
                })
            return {
                
                '_source': source
            }
        except:
            ex = traceback.format_exc()
            raise BrokenPage(ex)

    def get_date(self, tag):
        date_block = tag.xpath(
            'table//td[@valign="middle"]'
            '/div[@class="smalltext"]/text()'
        )
        if not date_block:
            date_block = tag.xpath(
                'table//td[@valign="middle"]'
                '/div[@class="smalltext"]/span[@class="edited"]/text()'
            )
        date = date_block[0].strip() if date_block else ""
        try:
            pattern = '%B %d, %Y, %I:%M:%S %p'
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except:
            traceback.print_exc()
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            'table//td[@class="poster_info"]'
            '/b/a/text()'
        )

        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(
           'table//div[@class="subject"]/a/text()'
        )
        title = title[0].strip() if title else None
        return title

    def get_post_text(self, tag):
        post_text = tag.xpath(
            'table//div[@class="post"]/text()'
        )

        post_text = "\n".join(
            [text.strip() for text in post_text if text.strip()]
        ) if post_text else ""
        return post_text.strip()

    def get_comment_id(self, tag):
        reply_block = tag.xpath(
            'table//td[@class="td_buttons"]'
            '/div/a/img[@class="reply_button"]'
        )
        if reply_block:
            return
        comment_block = tag.xpath(
            'table//td[@class="td_buttons"]'
            '/div/a/text()'
        )
        if comment_block:
            commentID = comment_block[0].split('#')[-1].replace(',', '')
            return commentID.replace(',', '')
        return ""

    def get_avatar(self, tag):
        avatar_block = tag.xpath(
            '//img[@class="avatar"]/@src'
        )
        if not avatar_block:
            return ""
        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""
        return name_match[0]
