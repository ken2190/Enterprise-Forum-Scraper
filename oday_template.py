import os
import re
from collections import OrderedDict
import traceback
import json
from lxml.html import fromstring


class BrokenPage(Exception):
    pass


class oday_parser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = parser_name
        self.files = self.get_filtered_files(files)
        self.folder_path = folder_path
        self.counter = 1
        self.data_dic = OrderedDict()
        self.distinct_files = set()
        self.output_folder = output_folder
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

    def file_read(self, template):
        with open(template) as f:
            return f.read()

    def get_next_template(self, template_counter):
        next_template = self.files[template_counter]
        file_name_only = next_template.split('/')[-1]
        match = self.thread_name_pattern.findall(file_name_only)
        if not match:
            return
        return match[0]

    def main(self):
        template_counter = 1
        comments = []
        for template in self.files:
            print(template)
            try:
                # read html file
                template_open = self.file_read(template)
                html_response = fromstring(template_open)
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern.findall(file_name_only)
                if not match:
                    continue
                self.thread_id = match[0]

                # ----------get next template --------
                try:
                    next_template = self.get_next_template(template_counter)
                    template_counter += 1

                    if next_template == self.thread_id:
                        final = False
                    else:
                        final = True
                except:
                    final = True
                # ------------check for new file or pagination file ------
                if self.thread_id not in self.distinct_files:
                    self.counter = 1
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
                    file_pointer = open(output_file, 'w')
                    self.write_json(file_pointer, data, initial=True)
                # extract comments
                comments.extend(self.extract_comments(template_open))

                if final:
                    comments = sorted(
                        comments, key=lambda k: int(k['commentID'])
                    )
                    for comment in comments:
                        self.write_json(file_pointer, comment)
                    comments = []
                    print('\nJson written in {}'.format(output_file))
                    print('----------------------------------------\n')
            except BrokenPage as ex:
                self.handle_error(template, ex)
            except:
                continue

    def handle_error(self, template, error_message):
        error_folder = "{}/Errors".format(self.output_folder)
        if not os.path.exists(error_folder):
            os.makedirs(error_folder)

        file_path = "{}/{}.txt".format(
            error_folder,
            template.split('/')[-1].rsplit('.', 1)[0]
        )
        with open(file_path, 'a') as file_pointer:
            file_pointer.write(str(error_message))

    def extract_comments(self, template_open):
        html_response = fromstring(template_open)
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
            comments.append({
                'pid': self.thread_id.replace('thread-', ''),
                'date': comment_date,
                'text': comment_text,
                'commentID': commentID,
                'user': user,
                'authorID': authorID,
            })
        return comments

    def header_data_extract(self, html_response, template):
        try:
            # ---------------extract header data ------------
            title = html_response.xpath(
                '//td[@class="thead"]/div/strong/text()'
            )
            title = title[0].strip() if title else None
            """
            white-space: nowrap; text-align: center; vertical-align: middle;
            white-space: nowrap; text-align: center; vertical-align: middle;
            """
            date = html_response.xpath(
                '//div[@id="posts"]//td[@style="'
                'white-space: nowrap; text-align: '
                'center; vertical-align: middle;"]'
                '/span/text()'
                )
            date = date[0].strip() if date else None
            if not date:
                text = "The specified thread does not exist"
                if html_response.xpath(
                  '//td[contains(text(), '
                  '"{}")]'.format(text)):
                    self.handle_error(template, text)
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
                'pid': self.thread_id.replace('thread-', ''),
                'title': title,
                'date': date,
                'author': author,
                'author_link': author_link,
                'text': post_text,
                'type': "post"
            }
        except:
            ex = traceback.format_exc()
            raise BrokenPage(ex)

    def write_json(self, file_pointer, data, initial=False):
        if not initial:
            file_pointer.write(',\n')
        json_file = json.dumps(data, indent=4)
        file_pointer.write(json_file)
