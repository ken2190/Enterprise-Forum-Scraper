# -- coding: utf-8 --
import re
import traceback
import utils
import datetime
import dateutil.parser as dparser
from lxml.html import fromstring

from .base_template import BaseTemplate, BrokenPage

class AgoraParser(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "agora market"
        self.thread_name_pattern1 = re.compile(
            r'index.php.topic[=,](\d+)'
        )
        self.thread_name_pattern2 = re.compile(
            r'(\d+).txt$'
        )
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.header_xpath = '//div[@class="post_wrapper"]'
        self.comment_block_xpath = 'div[@class="postarea"]//div[@class="smalltext"]/strong/text()'
        self.title_xpath = 'div[@class="postarea"]//h5/a/text()'
        self.date_xpath = 'div[@class="postarea"]//div[@class="smalltext"]/text()'
        self.date_pattern = "%B %d, %Y, %I:%M:%S %p"
        self.author_xpath =  'div[@class="poster"]/h4/a/text()'
        self.post_text_xpath = 'div[@class="postarea"]//div[@class="post"]//div[@class="inner"]/text()'
        self.comments_xpath = '//div[@class="post_wrapper"]'
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

    def get_html_response_1(self, file):
        with open(file, 'rb') as f:
            content = str(f.read())
            splitter = 'Content-Type: text/html; charset=UTF-8'
            content = content.split(splitter)[-1]
            content = content.replace('\\r', '')\
                             .replace('\\n', '')\
                             .replace('\\t', '')\
                             .strip()
            html_response = fromstring(content)

            return html_response

    def get_html_response_2(self, file):
        with open(file, 'rb') as f:
            content = str(f.read())
            content = content.replace('<-', '')
            html_response = fromstring(content)

            return html_response

    def main(self):
        comments = []
        output_file = None

        for index, template in enumerate(self.files):
            file_type = None
            print(template)
            try:
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern1.findall(file_name_only)
                # read html file
                if match:
                    html_response = self.get_html_response_1(template)
                    self.thread_id = match[0]
                    file_type = 1
                else:
                    match = self.thread_name_pattern2.findall(file_name_only)
                    if match:
                        html_response = self.get_html_response_2(template)
                        self.thread_id = match[0]
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
                    self.distinct_files.add(self.thread_id)

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
            comment_blocks = html_response.xpath(self.comments_xpath)
        else:
            whole_text = html_response.text
            comment_blocks = whole_text.split('Title: Re:')[1:]

        for index, comment_block in enumerate(comment_blocks, 1):
            user = self.get_author(comment_block, file_type)
            comment_text = self.get_post_text(comment_block, file_type)
            comment_date = self.get_date(comment_block, file_type)
            pid = self.thread_id
            avatar = self.get_avatar(comment_block, file_type)
            if file_type == 2:
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
            if file_type == 2:
                whole_text = html_response.text
                header = [whole_text.split('Title:')[1]]
            else:
                header = html_response.xpath(self.header_xpath)
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
        if file_type == 2:
            date_block = re.compile(r'Post by:.*? on (.*? \d+:\d+:\d+ [ap]m)')
            match = date_block.findall(tag)
            if match:
                date = match[0].strip()
        else:
            date = tag.xpath(self.date_xpath)
            date_pattern = re.compile(r'(.*[aApP][mM])')
            match = date_pattern.findall(date[-1])
            date = match[0].strip() if match else None

        try:
            date = datetime.datetime.strptime(date, self.date_pattern).timestamp()
            return str(date)
        except:
            try:
                date = dparser.parse(date).timestamp()
                return str(date)
            except:
                pass

        return ""

    def get_author(self, tag, file_type):
        if file_type == 2:
            author_block = re.compile(r'Post by: (.*?) on ')
            match = author_block.findall(tag)
            if match:
                return match[0].strip()
        else:
            return super().get_author(tag)

    def get_title(self, tag, file_type):
        if file_type == 2:
            title = tag.split('\\n')[0].strip()
            title = title.replace('\\t', ' ')
            return title
        else:
            return super().get_title(tag)

    def get_post_text(self, tag, file_type):
        if file_type == 2:
            post_block = re.compile(
                r'Post by:.*?\d+:\d+:\d+ [ap]m(.*)', re.DOTALL)
            match = post_block.findall(tag)
            if match:
                post_text = match[0].strip()
                post_text = post_text.replace('\\n', ' ').replace('\\t', ' ')
                return post_text
        else:
            return super().get_post_text(tag)

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        if comment_block:
            comment_pattern = re.compile(r'Reply #(\d+) on:')
            match = comment_pattern.findall(comment_block[0])
            comment_id = match[0] if match else ""

        return comment_id.replace(',', '')
