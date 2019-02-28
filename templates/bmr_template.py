import os
import re
from collections import OrderedDict
import traceback
import json
import utils
import datetime


class BrokenPage(Exception):
    pass


class BMRParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = parser_name
        self.files = self.get_filtered_files(files)
        self.folder_path = folder_path
        self.data_dic = OrderedDict()
        self.distinct_files = set()
        self.output_folder = output_folder
        self.error_folder = "{}/Errors".format(output_folder)
        self.thread_name_pattern = re.compile(r'(viewtopic\.php.*id=\d+)')
        self.thread_id = None
        # main function
        self.main()

    def get_filtered_files(self, files):
        final_files = list()
        for file in files:
            file_name_only = file.split('/')[-1]
            if file_name_only.startswith('viewtopic.php'):
                final_files.append(file)
        return sorted(final_files)

    def main(self):
        comments = []
        for index, template in enumerate(self.files):
            print(template)
            try:
                # read html file
                html_response = utils.get_html_response(template)
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern.findall(file_name_only)
                if not match:
                    continue
                self.thread_id = match[0]
                final = utils.is_file_final(
                    self.thread_id, self.thread_name_pattern, self.files, index
                )
                if self.thread_id not in self.distinct_files:
                    self.distinct_files.add(self.thread_id)

                    # header data extract
                    data = self.header_data_extract(html_response, template)
                    if not data:
                        continue

                    # write file
                    output_file = '{}/{}.json'.format(
                        str(self.output_folder),
                        self.thread_id.split('id=')[-1]
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
                    self.thread_id.split('id=')[-1],
                    self.error_folder,
                    ex
                )
            except:
                traceback.print_exc()
                continue

    def extract_comments(self, html_response):
        comments = list()
        comment_blocks = html_response.xpath(
          '//div[contains(@class, "replypost")]'
        )
        for comment_block in comment_blocks[1:]:

            user = self.get_author(comment_block)
            authorID = self.get_author_link(comment_block)
            commentID = self.get_comment_id(comment_block)
            if not commentID:
                continue
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            comments.append({
                
                '_source': {
                    'pid': self.thread_id.split('id=')[-1],
                    'date': comment_date,
                    'message': comment_text.strip(),
                    'cid': commentID,
                    'author': user,
                },
            })
        return comments

    def header_data_extract(self, html_response, template):
        try:
            title = self.get_title(html_response)

            # ---------------extract header data ------------
            header = html_response.xpath(
                '//div[@class="main-content main-topic"]/'
                'div[contains(@class,"firstpost")]'
            )
            if not header:
                return
            date = self.get_date(header[0])
            author = self.get_author(header[0])
            author_link = self.get_author_link(header[0])
            post_text = self.get_post_text(header[0])

            return {
                
                '_source': {
                    'pid': self.thread_id.split('id=')[-1],
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
                'div//span[@class="post-link"]'
                '/a/text()'
        )
        date = date[0].strip() if date else None
        try:
            pattern = '%Y-%m-%d %H:%M'
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except:
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            'div//span[@class="post-byline"]'
            '/em/a/text()'
        )
        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(
            '//h1[@class="main-title"]/a/text()'
        )
        title = title[0].strip() if title else None
        return title

    def get_author_link(self, tag):
        author_link = tag.xpath(
            'div//span[@class="post-byline"]'
            '/em/a/@href'
        )
        if author_link:
            pattern = re.compile(r'id=(\d+)')
            match = pattern.findall(author_link[0])
            author_link = match[0] if match else None
        return author_link

    def get_post_text(self, tag):
        post_text = None
        post_text_block = tag.xpath(
            'div//div[@class="entry-content"]/*'
        )
        post_text = "\n".join([
            post_text.xpath('string()') for post_text in post_text_block
        ])
        return post_text

    def get_comment_id(self, tag):
        commentID = tag.xpath(
            'div//span[@class="post-num"]/text()'
        )
        commentID = commentID[0].strip() if commentID else None

        # Exclude first comment as this is the post
        if commentID == "1":
            return
        return commentID.replace(',', '')
