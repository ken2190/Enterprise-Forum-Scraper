import re
from bs4 import BeautifulSoup
from collections import OrderedDict
import traceback
import json
from lxml.html import fromstring


class oday_parser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = parser_name
        self.files = self.get_filtered_files(files)
        # print(self.files)
        self.folder_path = folder_path
        self.counter = 1
        # self.data_dic = {}
        self.data_dic = OrderedDict()
        self.distinct_files = set()
        self.output_folder = output_folder
        self.thread_name_pattern = re.compile(r'(thread-\d+)')
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
        condition = True

        for template in self.files:
            print(template)
            try:
                # read html file
                template_open = self.file_read(template)

                # # parse file_name
                # file_name = template.split('/')[-1]\
                #                     .replace('.html', '')\
                #                     .replace('.htm', '')\
                #                     .split('-')[0]

                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern.findall(file_name_only)
                if not match:
                    continue
                file_name = match[0]
                # for css_selector
                soup = BeautifulSoup(template_open, 'html.parser')

                # ----------get next template --------
                try:
                    next_template = self.get_next_template(template_counter)
                    template_counter += 1

                    if next_template == file_name:
                        condition = False
                    else:
                        condition = True
                except:
                    condition = True

                # ------------check for new file or pagination file ------
                post_id = file_name
                comments = []
                if file_name not in self.distinct_files:
                    self.counter = 1
                    self.distinct_files.add(file_name)

                    # header data extract
                    title, date, author, author_link, post_text =\
                        self.header_data_extract(soup)

                    # write file
                    output_file = '{}/{}.json'.format(
                        str(self.output_folder), str(file_name)
                    )
                    f = open(output_file, 'w')
                    # create json file
                    self.create_json(
                        title,
                        date,
                        author,
                        author_link,
                        post_text,
                        post_id
                    )
                # extract comments
                self.extract_comments(template_open)

                if condition:
                    self.write_json(f, file_name)
            except:
                traceback.print_exc()
                continue

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
            user = user[0] if user else None
            user_link = user_block.xpath('strong/span/a/@href')
            user_link = user_link[0] if user_link else None

            commentID = text_block.xpath(
                'table//strong[contains(text(), "Post:")]/a/text()'
            )
            commentID = int(commentID[0].replace('#', '')) if commentID else None

            post_id = text_block.xpath(
                'table//strong[contains(text(), "Post:")]/a/@href'
            )
            if post_id:
                pattern = re.compile(r'.*-(\w+)\.html')
                match = pattern.findall(post_id[0])
                post_id = match[0]

            comment_text = text_block.xpath(
                'table//div[@class="post_body"]/text()'
            )
            comment_text = comment_text[0].strip() if comment_text else None

            comment_date = date_block.xpath('td/span[@class="smalltext"]/text()')
            comment_date = comment_date[0] if comment_date else None
            self.data_dic['comments'].append({
                'id': post_id,
                'commentID': commentID,
                'user': user,
                'user_link': user_link,
                'comment_date': comment_date,
                'comment_text': comment_text,
            })

        # # ---------------get all comments ---------------
        # for comment in soup.select('#posts [style="margin-top: 5px; "]'):
        #     comment_user = comment.select_one('tr strong').text
        #     comment_user_link = comment.select_one('tr strong a').get('href')
        #     comment_date = comment.select_one(
        #         'tr td[style="white-space: nowrap; '
        #         'text-align: center; vertical-align: middle;"]').text
        #     comment_text = comment.select_one('.post_body').text.strip()

        #     comment_dic = {
        #         'id': post_id,
        #         'commentID': self.counter,
        #         'user': comment_user,
        #         'user_link': comment_user_link,
        #         'comment_date': comment_date,
        #         'comment_text': comment_text,
        #          }
        #     # append comment dic into list
        #     comments.append(comment_dic)
        #     self.counter += 1

    def header_data_extract(self, soup):
        # ---------------extract header data ------------
        title = soup.select_one('title').text
        date = soup.select_one(
            '#posts [style="border-top-width: 0; "] '
            'tr td[style="white-space: nowrap; text-align: '
            'center; vertical-align: middle;"]').text
        author = soup.select_one(
            '#posts [style="border-top-width: 0; "] tr strong').text
        author_link = soup.select_one(
            '#posts [style="border-top-width: 0; "] tr strong a').get('href')
        post_text = soup.select_one(
            '#posts [style="border-top-width: 0; "] .post_body').text.strip()
        post_id = soup.select_one(
            '#posts [style="border-top-width: 0; "]').get('id')

        return title, date, author, author_link, post_text

    def create_json(self, title, date, author, author_link,
                    post_text, post_id):
        self.data_dic['id'] = post_id
        self.data_dic['title'] = title
        self.data_dic['date'] = date
        self.data_dic['author'] = author
        self.data_dic['author_link'] = author_link
        self.data_dic['post_text'] = post_text
        self.data_dic['comments'] = []

    def write_comment_json(self, comments):
        self.data_dic['comments'] = comments

    def write_json(self, f, file_name):
        self.data_dic['comments'] = sorted(
            self.data_dic['comments'], key=lambda k: k['commentID']
        )
        json_file = json.dumps(self.data_dic, indent=4)
        f.write(json_file)
        print ('%s.json done..!' % file_name)

