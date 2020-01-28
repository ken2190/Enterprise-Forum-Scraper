# -- coding: utf-8 --
import os
import re
import traceback
import json
import datetime
import utils
import dateutil.parser as dparser


class BrokenPage(Exception):
    pass


class L33TParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = "l33t.su"
        self.output_folder = output_folder
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'avatar=(\w+\.\w+)$')
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
                pagination = self.pagination_pattern.findall(file_name_only)
                if pagination:
                    pagination = int(pagination[0])
                final = utils.is_file_final(
                    self.thread_id,
                    self.thread_name_pattern,
                    self.files,
                    index
                )
                if self.thread_id not in self.distinct_files and\
                   not output_file:

                    # header data extract
                    data = self.header_data_extract(
                        html_response, template)
                    self.index = (pagination-1)*10 or 1
                    if not data or not pagination == 1:
                        comments.extend(
                            self.extract_comments(html_response, pagination))
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
                    self.extract_comments(html_response, pagination))

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

    def extract_comments(self, html_response, pagination):
        comments = list()
        comment_blocks = html_response.xpath(
          '//div[@class="inner"][div[@class="postbody"]]'
        )
        comment_blocks = comment_blocks[1:]\
            if pagination == 1 else comment_blocks
        for comment_block in comment_blocks:
            user = self.get_author(comment_block)
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            pid = self.thread_id
            avatar = self.get_avatar(comment_block)

            source = {
                'forum': self.parser_name,
                'pid': pid,
                'message': comment_text.strip(),
                'cid': str(self.index),
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
            self.index += 1
        return comments

    def header_data_extract(self, html_response, template):
        try:

            # ---------------extract header data ------------
            header = html_response.xpath(
                '//div[@class="inner"][div[@class="postbody"]]'
            )
            if not header:
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

    def get_date(self, tag):
        date = tag.xpath(
            'div//p[@class="author"]/text()'
        )
        date = date[-1].strip() if date else None
        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except:
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            'div//p[@class="author"]/span/strong/a/text()'
        )
        if not author:
            author = tag.xpath(
                'div/h4/text()'
            )
        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(
            'div//h3/a/text()'
        )
        title = title[0].strip() if title else None
        return title

    def get_post_text(self, tag):
        post_text = tag.xpath(
            'div//div[@class="content"]/'
            '/descendant::text()['
            'not(ancestor::blockquote)]'
        )
        post_text = "\n".join(
            [text.strip() for text in post_text]
        ) if post_text else ""
        return post_text

    def get_avatar(self, tag):
        avatar_block = tag.xpath(
            'dl//img[@class="avatar"]/@src'
        )
        if not avatar_block:
            return ""
        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""
        return name_match[0]
