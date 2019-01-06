import os
import re
from collections import OrderedDict
import traceback
import json
import utils


class BrokenPage(Exception):
    pass


class bmr_parser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = parser_name
        self.files = self.get_filtered_files(files)
        self.folder_path = folder_path
        self.data_dic = OrderedDict()
        self.distinct_files = set()
        self.output_folder = output_folder
        self.error_folder = "{}/Errors".format(output_folder)
        self.thread_name_pattern = re.compile(r'(viewtopic\.php\?pid=\d+)')
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
                        self.thread_id.split('pid=')[-1]
                    )
                    file_pointer = open(output_file, 'w')
                    utils.write_json(file_pointer, data)
                # extract comments
                comments.extend(self.extract_comments(html_response))

                if final:
                    utils.write_comments(file_pointer, comments, output_file)
                    comments = []
            except BrokenPage as ex:
                utils.handle_error(
                    self.thread_id.split('pid=')[-1],
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

            user = comment_block.xpath(
                'div//span[@class="post-byline"]'
                '/em/a/text()'
            )
            user = user[0].strip() if user else None

            authorID = None
            author_link = comment_block.xpath(
                'div//span[@class="post-byline"]'
                '/em/a/@href'
            )
            if author_link:
                pattern = re.compile(r'id=(\d+)')
                match = pattern.findall(author_link[0])
                authorID = match[0] if match else None

            commentID = comment_block.xpath(
                'div//span[@class="post-num"]/text()'
            )
            commentID = commentID[0].strip() if commentID else None

            # Exclude first comment as this is the post
            if commentID == "1":
                continue
            try:
                commentID = str(int(commentID)-1)
            except:
                pass

            comment_text = None
            comment_text_block = comment_block.xpath(
                'div//div[@class="entry-content"]/*'
            )
            comment_text = "\n".join([
                comment_text.xpath('string()')
                for comment_text in comment_text_block
            ])
            comment_date = comment_block.xpath(
                'div//span[@class="post-link"]'
                '/a/text()'
            )
            comment_date = comment_date[0] if comment_date else None
            comments.append({
                'pid': self.thread_id.split('pid=')[-1],
                'date': comment_date,
                'text': comment_text.strip(),
                'commentID': commentID,
                'user': user,
                'authorID': authorID,
            })
        return comments

    def header_data_extract(self, html_response, template):
        try:
            title = html_response.xpath(
                '//h1[@class="main-title"]/a/text()'
            )
            title = title[0].strip() if title else None

            # ---------------extract header data ------------
            header = html_response.xpath(
                '//div[@class="main-content main-topic"]/'
                'div[contains(@class,"firstpost")]'
            )
            if not header:
                return
            date = header[0].xpath(
                'div//span[@class="post-link"]'
                '/a/text()'
            )
            date = date[0].strip() if date else None
            author = header[0].xpath(
                'div//span[@class="post-byline"]'
                '/em/a/text()'
            )
            author = author[0].strip() if author else None

            author_link = header[0].xpath(
                'div//span[@class="post-byline"]'
                '/em/a/@href'
            )
            if author_link:
                pattern = re.compile(r'id=(\d+)')
                match = pattern.findall(author_link[0])
                author_link = match[0] if match else None

            post_text = None
            post_text_block = header[0].xpath(
                'div//div[@class="entry-content"]/*'
            )
            post_text = "\n".join([
                post_text.xpath('string()') for post_text in post_text_block
            ])

            return {
                'pid': self.thread_id.split('pid=')[-1],
                'title': title,
                'date': date,
                'author': author,
                'author_link': author_link,
                'text': post_text.strip(),
                'type': "post"
            }
        except:
            ex = traceback.format_exc()
            raise BrokenPage(ex)
