# -- coding: utf-8 --
import os
import re
from collections import OrderedDict
import traceback
import json
import datetime
import utils


class BrokenPage(Exception):
    pass


class DarkodeParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = parser_name
        self.output_folder = output_folder
        self.thread_name_pattern = re.compile(
            r'(\d+).*html'
        )
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
          '//table[@class="forumline"]/tbody/tr'
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
                '//table[@class="forumline"]/tbody/tr'
            )
            if not header:
                return
            title = self.get_title(html_response)
            date = self.get_date(header[2])
            author = self.get_author(header[1])
            post_text = self.get_post_text(header[1])
            pid = self.thread_id
            return {
                
                '_source': {
                    'pid': pid,
                    's': title,
                    'd': date,
                    'a': author,
                    'm': post_text.strip(),
                }
            }
        except:
            ex = traceback.format_exc()
            raise BrokenPage(ex)

    def get_date(self, tag):
        date = tag.xpath(
            'td/text()'
        )
        date = date[0].strip() if date else ""
        if not date:
            return ""
        try:
            pattern = "%a %b %d, %Y %H:%M %p"
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except:
            traceback.print_exc()
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            'td//span[@class="postername"]//strong/text()'
        )
        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(
            '//td[@class="forumheader-mid"]/a/text()'
        )
        title = title[0].strip() if title else None
        return title

    def get_post_text(self, tag):
        post_text = tag.xpath(
            'td[@class="row1" or @class="row2"]'
            '//td[@colspan="2"]/text()'
        )
        post_text = "\n".join(
            [text.strip() for text in post_text]
        ) if post_text else ""
        return post_text
