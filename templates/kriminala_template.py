# -- coding: utf-8 --
import os
import re
import traceback
import json
import locale
import datetime
import utils
import dateutil.parser as dparser


class BrokenPage(Exception):
    pass


class KriminalaParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "kriminala.net"
        self.output_folder = output_folder
        self.date_pattern = re.compile(r'Добавлено:(.*)[ap]m', re.I)
        self.thread_name_pattern1 = re.compile(
            r'\!topic(\d+).*html'
        )
        self.thread_name_pattern2 = re.compile(
            r'\!viewtopic\.php.*?t=(\d+).*html'
        )

        self.avatar_name_pattern = re.compile(r'avatars/(\w+\.\w+)$')
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
                lambda x: self.thread_name_pattern1.search(
                    x.split('/')[-1]) is not None,
                files
            )
        )
        filtered_files_2 = list(
            filter(
                lambda x: self.thread_name_pattern2.search(
                    x.split('/')[-1]) is not None,
                files
            )
        )
        sorted_files_1 = sorted(
            filtered_files_1,
            key=lambda x: int(self.thread_name_pattern1.search(
                x.split('/')[-1]).group(1)))
        sorted_files_2 = sorted(
            filtered_files_2,
            key=lambda x: int(self.thread_name_pattern2.search(
                x.split('/')[-1]).group(1)))
        return sorted_files_1 + sorted_files_2

    def main(self):
        comments = []
        output_file = None
        self.index = 1
        for index, template in enumerate(self.files):
            print(template)
            try:
                html_response = utils.get_html_response(template)
                file_name_only = template.split('/')[-1]
                match_type = 1
                pattern = self.thread_name_pattern1
                match = pattern.findall(file_name_only)
                if not match:
                    match_type = 2
                    pattern = self.thread_name_pattern2
                    match = pattern.findall(file_name_only)
                if not match:
                    continue
                pid = self.thread_id = match[0]
                final = utils.is_file_final(
                    self.thread_id,
                    pattern,
                    self.files,
                    index
                )
                if self.thread_id not in self.distinct_files and\
                   not output_file:

                    # header data extract
                    data = self.header_data_extract(
                        html_response, template)
                    if not data:
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
                    self.index = 1
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
          '//a[@name and @id]'
        )
        comment_blocks = comment_blocks[1:] if self.index == 1\
            else comment_blocks
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
                '//a[@name and @id]'
            )
            if not header:
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
            'following-sibling::table[1]'
            '//span[@class="postdetails"]/text()'
        )
        if not date:
            date = tag.xpath(
                'following-sibling::table[1]'
                '//td[@nowrap and contains(string(), "Добавлено")]/text()'
            )
        if not date:
            return ''
        match = self.date_pattern.findall(date[-1])
        if not match:
            date = tag.xpath(
                'following-sibling::table[3]'
                '//span[@class="offcomment"]/text()'
            )
        if not date:
            return ''
        match = self.date_pattern.findall(date[-1])
        if not match:
            return ''
        date = match[0].strip()
        try:
            pattern = "%a %b %d, %Y %H:%M"
            return str(datetime.datetime.strptime(date, pattern).timestamp())
        except:
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            'following-sibling::table[1]'
            '//td[@class="nav"]/span[@style="color:"]/text()'
        )
        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(
            '//h1/a[@class="maintitle"]/text()'
        )
        title = title[0].strip() if title else None
        return title

    def get_post_text(self, tag):
        post_text_block = tag.xpath(
            'following-sibling::table[2]//td[@class="postbody"]/descendant::text()'
        )
        if not post_text_block:
            return ''
        post_text = "\n".join([
            t.strip() for t in post_text_block if t.strip()
        ])
        return post_text if post_text else ''

        # if not post_text_block[-1].xpath('text()'):
        #     post_text_block = tag.xpath(
        #         'following-sibling::table[2]//td[@class="postbody"]/span[@class="postbody"]'
        #     )

        # if not post_text_block:
        #     post_text_block = tag.xpath(
        #         'following-sibling::table[2]//font/span'
        #     )
        # text = ''
        # for p in post_text_block:
        #     post_text = "\n".join([
        #         t.strip() for t in p.xpath('descendant::text()') if t.strip()
        #     ])
        #     text += post_text
        # return text

    def get_avatar(self, tag):
        avatar_block = tag.xpath(
            'following-sibling::table[2]//img[@class="avatar"]/@src'
        )
        if not avatar_block:
            return ""
        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""
        return name_match[0]
