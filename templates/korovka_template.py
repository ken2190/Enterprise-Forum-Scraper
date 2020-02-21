# -- coding: utf-8 --
import os
import re
import traceback
import json
import datetime
import utils
import dateutil.parser as dparser
from lxml.html import fromstring


class BrokenPage(Exception):
    pass


class KorovkaParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = "korokova.cc"
        self.output_folder = output_folder
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'u=(\d+)')
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
            key=lambda x: (
                int(self.thread_name_pattern.search(x).group(1)),
                int(self.pagination_pattern.search(x).group(1))
            ))

        return sorted_files

    def get_html_response(self, template):
        """
        returns the html response from the `template` contents
        """
        with open(template, 'r') as f:
            content = f.read()
            try:
                html_response = fromstring(content)
            except ParserError as ex:
                return
            return html_response

    def main(self):
        comments = []
        output_file = None
        for index, template in enumerate(self.files):
            print(template)
            try:
                html_response = self.get_html_response(
                    template)
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
            except Exception:
                traceback.print_exc()
                continue

    def extract_comments(self, html_response, pagination):
        comments = list()
        comment_blocks = html_response.xpath(
          '//table[contains(@id, "post")]'
        )
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

    def header_data_extract(self, html_response, template):
        try:

            # ---------------extract header data ------------
            header = html_response.xpath(
                '//table[contains(@id, "post")]'
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
        except Exception:
            ex = traceback.format_exc()
            raise BrokenPage(ex)

    def get_date(self, tag):
        date_block = tag.xpath(
            'tr//td/a[contains(@name, "post")]/following-sibling::text()')
        date = ""
        if date_block:
            date = [d.strip() for d in date_block if d.strip()][0]

        try:
            pattern = '%d.%m.%Y, %H:%M'
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except Exception:
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            'tr//a[@class="bigusername"]/b/span/text()'
        )
        if not author:
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
        if not author:
            author = tag.xpath(
                'tr//a[@class="bigusername"]/s/b/span/text()'
            )
        if not author:
            author = tag.xpath(
                'tr//a[@class="bigusername"]/b/text()'
            )

        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(
            '//td[@class="navbar"]/a/following-sibling::strong[1]/text()'
        )
        title = title[0].strip() if title else None
        return title

    def get_post_text(self, tag):
        post_text_block = tag.xpath(
            'tr//div[contains(@id, "post_message_")]/div[@class="pmessage"]'
            '/descendant::text()[not(ancestor::div'
            '[@style="margin:20px; margin-top:5px; "])]'
        )
        post_text = " ".join([
            post_text.strip() for post_text in post_text_block
        ])
        return post_text.strip()

    def get_avatar(self, tag):
        avatar_block = tag.xpath(
            'tr//a[contains(@href, "member.php?u=") and img/@src]/@href'
        )
        if not avatar_block:
            return ""
        match = self.avatar_name_pattern.findall(avatar_block[0])
        if not match:
            return
        return match[0] + '.jpg'

    def get_comment_id(self, tag):
        comment_block = tag.xpath(
            'tr//td/a[contains(@id, "postcount")]/strong/text()')
        if not comment_block:
            return ''
        pattern = re.compile(r'\d+')
        match = pattern.findall(comment_block[0])
        if not match:
            return
        return match[0]
