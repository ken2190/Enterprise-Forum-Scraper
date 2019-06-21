# -- coding: utf-8 --
import os
import re
import traceback
import json
import utils
import datetime
import dateutil.parser as dparser
from lxml.html import fromstring


class BrokenPage(Exception):
    pass


class NulledBBParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = parser_name
        self.output_folder = output_folder
        self.thread_name_pattern = re.compile(
            r'(.*)-\d+\.html$'
        )
        self.pagination_pattern = re.compile(
            r'-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(files)
        self.folder_path = folder_path
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
                pid = self.thread_id = str(
                    int.from_bytes(
                        match[0].encode('utf-8'), byteorder='big'
                    ) % (10 ** 7)
                )
                pagination = self.pagination_pattern.findall(file_name_only)
                if pagination:
                    pagination = int(pagination[0])
                final = utils.is_file_final(
                    match[0],
                    self.thread_name_pattern,
                    self.files,
                    index
                )
                if self.thread_id not in self.distinct_files and\
                   not output_file:

                    # header data extract
                    data = self.header_data_extract(
                        html_response, template)
                    if not data or not pagination == 1:
                        comments.extend(
                            self.extract_comments(html_response))
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
                comments.extend(
                    self.extract_comments(html_response))

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
          '//div[@class="wrapper"]/div[1][@class="table-wrap"]'
        )
        # print(comment_blocks)
        for index, comment_block in enumerate(comment_blocks, 1):
            user = self.get_author(comment_block)
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            pid = self.thread_id
            avatar = self.get_avatar(comment_block)
            comment_id = self.get_comment_id(comment_block)
            if not comment_id or comment_id == "1":
                continue
            source = {
                'forum': self.parser_name,
                'pid': pid,
                'message': comment_text.strip(),
                'cid': comment_id,
                'author': user,
            }
            if comment_date:
                source.update({
                    'd': comment_date
                })
            if avatar:
                source.update({
                    'img': avatar
                })
            comments.append({
                '_source': source,
            })
        return comments

    def header_data_extract(self, html_response, template):
        try:

            # ---------------extract header data ------------
            header = html_response.xpath(
                '//div[@class="wrapper"]/div[1][@class="table-wrap"]'
            )
            if not header:
                return
            if not self.get_comment_id(header[0]) == "1":
                return
            title = self.get_title(html_response)
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
            }
            if date:
                source.update({
                   'd': date
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
        date_block = tag.xpath(
            'div//div[contains(string(), "Posted:")]/text()'
        )
        date = [d.strip() for d in date_block if d.strip()]
        if not date:
            return
        date = date[0].replace('Posted:', '').strip()
        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except:
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            'div//div[contains(@class, "postbit-username")]//span/text()'
        )
        if not author:
            author = tag.xpath(
                'div//div[@class="message-userDetails"]/h4/a/text()'
            )

        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(
            '//div[@class="table-wrap"]//h1/text()'
        )
        title = title[0].strip() if title else None
        return title

    def get_post_text(self, tag):
        post_text_block = tag.xpath(
            'div//div[@class="postbit-message-content"]'
            '/descendant::text()[not(ancestor::blockquote)]'
        )
        post_text = " ".join([
            post_text.strip() for post_text in post_text_block
        ])
        return post_text.strip()

    def get_avatar(self, tag):
        avatar_block = tag.xpath(
            'div//div[@class="author_avatar"]/a/img/@src'
        )
        if not avatar_block:
            return ""
        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""
        return name_match[0]

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(
            'div//div[@class="right"]/strong/a/text()'
        )
        if comment_block:
            comment_id = comment_block[-1].split('#')[-1]

        return comment_id.replace(',', '').strip()
