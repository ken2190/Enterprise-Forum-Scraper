import os
import shutil
import re
from collections import OrderedDict
import traceback
import json
import utils
import datetime


class BrokenPage(Exception):
    pass


class EvolutionParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = parser_name
        self.output_folder = output_folder
        self.files = self.get_filtered_files(files)
        self.folder_path = folder_path
        self.data_dic = OrderedDict()
        self.distinct_files = set()
        self.error_folder = "{}/Errors".format(output_folder)
        self.thread_name_pattern = re.compile(r'(viewtopic\.php.*id=\d+)')
        self.thread_id = None
        # main function
        self.main()

    def get_filtered_files(self, files):
        final_files = list()
        for file in files:
            if file.endswith('.txt'):
                saved_file = self.save_file(file)
                final_files.append(saved_file)
            else:
                file_name_only = file.split('/')[-1]
                if file_name_only.startswith('viewtopic.php'):
                    final_files.append(file)
        return sorted(final_files)

    def save_file(self, file):
        with open(file, 'rb') as f:
            content = str(f.read())
            content = content.split('SAMEORIGIN')[-1]
            content = content.replace('\\r', '')\
                             .replace('\\n', '')\
                             .replace('\\t', '')\
                             .strip()
            pattern = re.compile(r'(viewtopic.php.*).txt')
            new_file = pattern.findall(file)
            if new_file:
                new_file_path = "{}/{}".format(self.output_folder, 'Processed')
                if not os.path.exists(new_file_path):
                    os.makedirs(new_file_path)
                new_name = new_file[0]
                new_file_path = "{}/{}".format(new_file_path, new_name)
                with open(new_file_path, 'w') as f:
                    f.write(content)
                return new_file_path

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
                    file_pointer = open(output_file, 'w')
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
        self.remove_intermediate_folder()

    def remove_intermediate_folder(self,):
        path = "{}/{}".format(self.output_folder, 'Processed')
        shutil.rmtree(path)

    def extract_comments(self, html_response):
        comments = list()
        comment_blocks = html_response.xpath(
          '//div[@id="brdmain"]/div[@id and @id!="quickpost"]'
        )
        for comment_block in comment_blocks[1:]:

            user = self.get_author(comment_block)
            authorID = self.get_author_link(comment_block)
            if not authorID:
                authorID = ""
            commentID = self.get_comment_id(comment_block)
            if not commentID:
                continue
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            comments.append({
                'pid': self.thread_id.split('id=')[-1],
                'date': comment_date,
                'text': comment_text.strip(),
                'commentID': commentID,
                'user': user,
                'authorID': authorID,
            })
        return comments

    def header_data_extract(self, html_response, template):
        try:
            title = self.get_title(html_response)

            # ---------------extract header data ------------
            header = html_response.xpath(
                '//div[@id="brdmain"]/'
                'div[contains(@class,"blockpost1")]'
            )
            if not header:
                print('no header')
                return
            date = self.get_date(header[0])
            author = self.get_author(header[0])
            author_link = self.get_author_link(header[0])
            if not author_link:
                author_link = ""
            post_text = self.get_post_text(header[0])

            return {
                'pid': self.thread_id.split('id=')[-1],
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

    def get_date(self, tag):
        date = tag.xpath(
                'h2/span/a/text()'
        )
        date = date[0].strip() if date else None
        try:
            pattern = '%Y-%m-%d %H:%M:%S'
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except:
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            'div[@class="box"]//dt/strong/'
            '/a/span/text()'
        )
        if not author:
            author = tag.xpath(
                'div[@class="box"]//dt/strong/'
                '/span/text()'
            )

        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(
            '//div[@class="postright"]/h3/text()'
        )
        title = title[0].replace('Re:', '').strip() if title else None
        return title

    def get_author_link(self, tag):
        author_link = tag.xpath(
            'div[@class="box"]//dt/strong/'
            '/a/@href'
        )
        if author_link:
            pattern = re.compile(r'id=(\d+)')
            match = pattern.findall(author_link[0])
            author_link = match[0] if match else None
        return author_link

    def get_post_text(self, tag):
        post_text = None
        post_text_block = tag.xpath(
            'div//div[@class="postmsg"]/*'
        )
        post_text = "\n".join([
            post_text.xpath('string()') for post_text in post_text_block
        ])
        return post_text

    def get_comment_id(self, tag):
        commentID = tag.xpath(
            'h2/span/span/text()'
        )
        commentID = commentID[0].strip() if commentID else None
        commentID = commentID.replace(',', '').replace('#', '')
        # Exclude first comment as this is the post
        if commentID == "1":
            return
        return commentID.replace(',', '')
