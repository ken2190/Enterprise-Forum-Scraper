import os
import re
from collections import OrderedDict
import traceback
import json
import utils
import datetime


class BrokenPage(Exception):
    pass


class OdayParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = parser_name
        self.files = self.get_filtered_files(files)
        self.folder_path = folder_path
        self.data_dic = OrderedDict()
        self.distinct_files = set()
        self.output_folder = output_folder
        self.error_folder = "{}/Errors".format(output_folder)
        self.thread_name_pattern = re.compile(r'(thread-\d+)')
        self.thread_id = None
        # main function
        self.main()

    def get_filtered_files(self, files):
        final_files = list()
        for file in files:
            file_name_only = file.split('/')[-1]
            if file_name_only.startswith('thread-'):
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
                        self.thread_id.replace('thread-', '')
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
                    self.thread_id.replace('thread-', ''),
                    self.error_folder,
                    ex
                )
            except:
                traceback.print_exc()
                continue

    def extract_comments(self, html_response):
        comments = list()
        for comment_block in html_response.xpath(
          '//div[@id="posts"]/table'):
            user_block = comment_block.xpath('tr')[0].xpath('td')[0]
            text_block = comment_block.xpath('tr')[0].xpath('td')[1]
            date_block = comment_block.xpath('tr')[1]

            user = user_block.xpath('strong/span/a/text()')
            if not user:
                user = user_block.xpath('strong/span/text()')
            if not user:
                user = user_block.xpath('strong/span/a/span/text()')
            user = user[0] if user else None
            authorID = None
            user_link = user_block.xpath('strong/span/a/@href')
            if user_link:
                pattern = re.compile(r'/user-(\d+).')
                match = pattern.findall(user_link[0])
                authorID = match[0] if match else None

            commentID = text_block.xpath(
                'table//strong[contains(text(), "Post:")]/a/text()'
            )
            commentID = commentID[0].replace('#', '') if commentID else None

            # Exclude first comment as this is the post
            if commentID == "1":
                continue
            try:
                commentID = str(int(commentID)-1)
            except:
                pass

            comment_text = text_block.xpath(
                'table//div[@class="post_body"]/text()'
            )
            comment_text = "\n".join(
                [comment.strip() for comment in comment_text if comment]
            )

            comment_date = date_block.xpath(
                'td/span[@class="smalltext"]/text()'
            )
            comment_date = comment_date[0] if comment_date else None
            try:
                pattern = '%m-%d-%Y'
                comment_date = str(datetime.datetime
                                   .strptime(comment_date, pattern)
                                   .timestamp())
            except:
                comment_date = ""
            comments.append({
                
                '_source': {
                    'pid': self.thread_id.replace('thread-', ''),
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
            title = html_response.xpath(
                '//td[@class="thead"]/div/strong/text()'
            )
            title = title[0].strip() if title else None
            date = html_response.xpath(
                '//div[@id="posts"]//td[@style="'
                'white-space: nowrap; text-align: '
                'center; vertical-align: middle;"]'
                '/span/text()'
                )
            date = date[0].strip() if date else None
            try:
                pattern = '%m-%d-%Y'
                date = str(datetime.datetime
                           .strptime(date, pattern)
                           .timestamp())
            except:
                date = ""
            if not date:
                text = "The specified thread does not exist"
                if html_response.xpath(
                  '//td[contains(text(), '
                  '"{}")]'.format(text)):
                    utils.handle_error(
                        self.thread_id.replace('thread-', ''),
                        self.error_folder,
                        text
                    )
                    return
            author = html_response.xpath(
                '//div[@id="posts"]//table[@style="'
                'border-top-width: 0; "]//'
                'span[@class="largetext"]/a/text()')
            author = author[0].strip() if author else None

            author_link = html_response.xpath(
                '//div[@id="posts"]//table[@style="'
                'border-top-width: 0; "]//'
                'span[@class="largetext"]/a/@href')
            if author_link:
                pattern = re.compile(r'/user-(\d+).')
                match = pattern.findall(author_link[0])
                author_link = match[0] if match else None

            post_text = None
            post_text_block = html_response.xpath(
                '//table//div[@class="post_body"]'
            )
            if post_text_block:
                post_text = post_text_block[0].xpath('text()')\

                post_text = "\n".join(
                    [post.strip() for post in post_text if post]
                )
            return {
                
                '_source': {
                    'pid': self.thread_id.replace('thread-', ''),
                    'subject': title,
                    'date': date,
                    'author': author,
                    'message': post_text.strip(),
                }
            }
        except:
            ex = traceback.format_exc()
            raise BrokenPage(ex)
