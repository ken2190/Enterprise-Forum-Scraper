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


class KickAssParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = parser_name
        self.output_folder = output_folder
        self.thread_name_pattern = re.compile(
            r'(\d+).*html'
        )
        self.uid_pattern = re.compile(
            r'UID-(\d+)\.html'
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

    def extract_user_profile(self, html_response):
        data = dict()
        username = html_response.xpath(
            '//fieldset//span[@class="largetext"]'
            '//strong/text()'
        )
        if username:
            data.update({
                'username': username[0].strip()
            })
        jabber_id = html_response.xpath(
            '//td[strong[contains(text(), "Jabber ID:")]]'
            '/following-sibling::td[1]/text()'
        )
        if jabber_id:
            data.update({
                'jabberID': jabber_id[0].strip()
            })
        pgp_key_block = html_response.xpath(
            '//td[strong[contains(text(), "PGP Public Key:")]]'
            '/following-sibling::td[1]'
        )
        pgp_key = "".join([
            pgp_key.xpath('string()') for pgp_key in pgp_key_block
        ])
        data.update({
            'PGPKey': pgp_key.strip()
        })
        return data

    def process_user_profile(self, uid, html_response):
        data = {
            'userID': uid
        }
        additional_data = self.extract_user_profile(html_response)
        if not additional_data:
            return
        data.update(additional_data)
        output_file = '{}/UID-{}.json'.format(
            str(self.output_folder),
            uid
        )
        with open(output_file, 'w', encoding='utf-8') as file_pointer:
            utils.write_json(file_pointer, data)
            print('\nJson written in {}'.format(output_file))
            print('----------------------------------------\n')

    def main(self):
        comments = []
        output_file = None
        for index, template in enumerate(self.files):
            print(template)
            try:
                html_response = utils.get_html_response(template)
                file_name_only = template.split('/')[-1]
                uid_match = self.uid_pattern.findall(file_name_only)
                if uid_match:
                    self.process_user_profile(uid_match[0], html_response)
                    continue
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
          '//div[contains(@class,"post classic")]'
        )
        for comment_block in comment_blocks:
            user = self.get_author(comment_block)
            authorID = self.get_author_link(comment_block)
            commentID = self.get_comment_id(comment_block)
            if not commentID or commentID == "1":
                continue
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            pid = self.thread_id
            comments.append({
                
                '_source': {
                    'pid': pid,
                    'date': comment_date,
                    'message': comment_text.strip(),
                    'cid': commentID,
                    'author': user,
                },
            })
        return comments

    def header_data_extract(self, html_response, template):
        try:

            # ---------------extract header data ------------
            header = html_response.xpath(
                '//div[contains(@class,"post classic")]'
            )
            if not header:
                return
            if not self.get_comment_id(header[0]) == "1":
                return
            title = self.get_title(header[0])
            date = self.get_date(header[0])
            author = self.get_author(header[0])
            author_link = self.get_author_link(header[0])
            post_text = self.get_post_text(header[0])
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
            'div//span[@class="post-link"]/a/text()'
        )
        date = date[0].strip() if date else ""
        if not date:
            return ""
        try:
            pattern = '%Y-%m-%d %H:%M:%S'
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except:
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            'div//div[@class="author_information"]//a/span/strong/text()'
        )
        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(
            '//span[@class="active"]/text()'
        )
        title = title[0].strip() if title else None
        return title

    def get_author_link(self, tag):
        author_link = tag.xpath(
            'div//div[@class="author_information"]//a/@href'
        )
        if author_link:
            pattern = re.compile(r'id=(\d+)')
            match = pattern.findall(author_link[0])
            author_link = match[0] if match else None
        return author_link

    def get_post_text(self, tag):
        post_text = tag.xpath(
            'div[@class="post_content"]'
            '/div[@class="post_body scaleimages"]'
        )
        post_text = post_text[0].xpath('string()')\
            if post_text else ""
        return post_text

    def get_comment_id(self, tag):
        commentID = ""
        comment_block = tag.xpath(
            'div[@class="post_content"]//strong/a/text()'
        )
        commentID = comment_block[0].split('#')[-1].strip()\
            if comment_block else ""
        return commentID.replace(',', '')
