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


class SilkRoad1Parser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = parser_name
        self.output_folder = output_folder
        self.thread_name_pattern1 = re.compile(
            r'thread_(\d+).*html'
        )
        self.thread_name_pattern2 = re.compile(
            r'.*topic=(\d+)'
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
        filtered_files_1 = list(
            filter(
                lambda x: self.thread_name_pattern1.search(x) is not None,
                files
            )
        )
        sorted_files_1 = sorted(
            filtered_files_1,
            key=lambda x: int(self.thread_name_pattern1.search(x).group(1)))

        filtered_files_2 = list(
            filter(
                lambda x: self.thread_name_pattern2.search(x) is not None,
                files
            )
        )
        sorted_files_2 = sorted(
            filtered_files_2,
            key=lambda x: int(self.thread_name_pattern2.search(x).group(1)))

        return sorted_files_1 + sorted_files_2

    def main(self):
        comments = []
        output_file = None
        for index, template in enumerate(self.files):
            file_type = None
            print(template)
            try:
                html_response = utils.get_html_response(template)
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern1.findall(file_name_only)
                if match:
                    file_type = 1
                else:
                    match = self.thread_name_pattern2.findall(file_name_only)
                    if match and template.endswith('.html'):
                        file_type = 1
                    elif match:
                        file_type = 2
                if not file_type:
                    continue
                pid = self.thread_id = match[0]
                if file_type == 1:
                    final = utils.is_file_final(
                        self.thread_id,
                        self.thread_name_pattern1,
                        self.files,
                        index
                    )
                else:
                    final = utils.is_file_final(
                        self.thread_id,
                        self.thread_name_pattern2,
                        self.files,
                        index
                    )
                if self.thread_id not in self.distinct_files and\
                   not output_file:

                    # header data extract
                    data = self.header_data_extract(
                        html_response, template, file_type)
                    if not data:
                        comments.extend(
                            self.extract_comments(html_response, file_type))
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
                    self.extract_comments(html_response, file_type))

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

    def extract_comments(self, html_response, file_type):
        comments = list()
        if file_type == 1:
            comment_blocks = html_response.xpath(
              '//dl[@id="posts"]/'
              'dt[@class="postheader"]'
            )
            comment_blocks = comment_blocks[1:]
        else:
            comment_blocks = html_response.xpath(
              '//div[@class="post_wrapper"]'
            )
        # print(comment_blocks)
        for index, comment_block in enumerate(comment_blocks, 1):
            user = self.get_author(comment_block, file_type)
            comment_text = self.get_post_text(comment_block, file_type)
            comment_date = self.get_date(comment_block, file_type)
            pid = self.thread_id
            avatar = self.get_avatar(comment_block, file_type)
            if file_type == 1:
                comment_id = str(index)
            else:
                comment_id = self.get_comment_id(comment_block)
                if not comment_id:
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

    def header_data_extract(self, html_response, template, file_type):
        try:

            # ---------------extract header data ------------
            if file_type == 1:
                header = html_response.xpath(
                    '//dl[@id="posts"]/'
                    'dt[@class="postheader"]'
                )
            else:
                header = html_response.xpath(
                    '//div[@class="post_wrapper"]'
                )
                if self.get_comment_id(header[0]):
                    return
            if not header:
                return
            title = self.get_title(header[0], file_type)
            date = self.get_date(header[0], file_type)
            author = self.get_author(header[0], file_type)
            post_text = self.get_post_text(header[0], file_type)
            pid = self.thread_id
            avatar = self.get_avatar(header[0], file_type)
            source = {
                'forum': self.parser_name,
                'pid': pid,
                'subject': title,
                'author': author,
                'message': post_text.strip(),
            }
            if date:
                source.update({
                   'date': date
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

    def get_date(self, tag, file_type):
        date = ""
        if file_type == 1:
            date_block = tag.xpath(
                'strong/text()'
            )
            if len(date_block) == 3:
                date = date_block[2].strip()
        else:
            date = tag.xpath(
                'div//div[@class="smalltext"]/text()'
            )
            date_pattern = re.compile(r'(.*[aApP][mM])')
            match = date_pattern.findall(date[-1])
            date = match[0].strip() if match else None

        try:
            pattern = "%B %d, %Y, %I:%M %p"
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except:
            return ""

    def get_author(self, tag, file_type):
        if file_type == 1:
            author = tag.xpath(
                'strong/text()'
            )
            if len(author) == 3:
                author = author[1].strip()
                return author
        else:
            author = tag.xpath(
                'div[@class="poster"]'
                '/h4/a/text()'
            )
            author = author[0].strip() if author else None
        return author

    def get_title(self, tag, file_type):
        if file_type == 1:
            title = tag.xpath(
                'strong/text()'
            )
            if len(title) == 3:
                title = title[0].strip()
                return title
        else:
            title = tag.xpath(
                'div//h5/a/text()'
            )
            title = title[0].strip() if title else None
        return title

    def get_post_text(self, tag, file_type):
        if file_type == 1:
            post_text_block = tag.xpath(
                'following-sibling::dd[1]'
            )
        else:
            pass
            post_text_block = tag.xpath(
                'div//div[@class="post"]/'
                '/div[@class="inner"]'
            )
        post_text = "\n".join([
            post_text.xpath('string()') for post_text in post_text_block
        ])
        return post_text.strip()

    def get_avatar(self, tag, file_type):
        return
        if file_type == 1:
            pass
        else:
            pass
        avatar_block = tag.xpath(
            'div[@class="elgg-image-block clearfix thewire-post"]//img/@src'
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
            'div[@class="postarea"]'
            '//div[@class="smalltext"]/strong/text()'
        )
        if comment_block:
            comment_pattern = re.compile(r'Reply #(\d+) on:')
            match = comment_pattern.findall(comment_block[0])
            comment_id = match[0] if match else ""

        return comment_id.replace(',', '')
