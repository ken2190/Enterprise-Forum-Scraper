import os
import re
from collections import OrderedDict
import traceback
import json
import utils
import datetime


class BrokenPage(Exception):
    pass


class TheRealDealParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = "therealdeal market"
        self.thread_name_pattern = re.compile(r'index\.php\?topic=(\d+)')
        self.order_info_pattern = re.compile(r'^(\d+)$')
        self.files = self.get_filtered_files(files)
        self.folder_path = folder_path
        self.data_dic = OrderedDict()
        self.distinct_files = set()
        self.output_folder = output_folder
        self.error_folder = "{}/Errors".format(output_folder)
        self.thread_id = None
        # main function
        self.main()

    def get_pid(self):
        pid_pattern = re.compile(r'topic=(\d+)')
        pid = pid_pattern.findall(self.thread_id)
        pid = pid[0] if pid else self.thread_id
        return pid

    def get_filtered_files(self, files):
        filtered_files_1 = list(
            filter(
                lambda x: self.thread_name_pattern.search(x) is not None,
                files
            )
        )

        sorted_files_1 = sorted(
            filtered_files_1,
            key=lambda x: int(self.thread_name_pattern.search(x).group(1)))

        filtered_files_2 = list(
            filter(
                lambda x: self.order_info_pattern
                              .search(x.split('/')[-1]) is not None,
                files
            )
        )

        sorted_files_2 = sorted(
            filtered_files_2,
            key=lambda x: int(self.order_info_pattern
                                  .search(x.split('/')[-1]).group(1)))

        return sorted_files_1 + sorted_files_2

    def extract_order_detail(self, html_response):
        data = dict()
        order_block = html_response.xpath(
            '//div[@id="order-details"]/div[1]')
        address_block = html_response.xpath(
            '//div[@id="order-details"]/div[2]')
        signature_block = html_response.xpath(
            '//div[@id="order-details"]/div[3]')
        seller = order_block[0].xpath(
            'div//div[@class="panel-heading"]/a/text()')
        if seller:
            data.update({
                'seller': seller[0].strip()
            })
        total = order_block[0].xpath(
            'div//td[strong[text()="Total"]]'
            '/following-sibling::td[1]/b/text()')
        if total:
            data.update({
                'price': total[0].split('BTC')[-1].strip()
            })
        escrow_address = address_block[0].xpath(
            'div//code[@id="addressCode"]/text()')
        if escrow_address:
            data.update({
                'escrowAddress': escrow_address[0].strip()
            })
        if signature_block:
            additional_address = signature_block[0].xpath(
                'form//div[@class="col-xs-6"]/text()')
            if additional_address and len(additional_address) == 2:
                data.update({
                    'feeAddress': additional_address[0].strip(),
                    'sellerBTCAddress': additional_address[1].strip()
                })
        return data

    def process_order_details(self, order_id, html_response):
        data = {
            'orderNumber': order_id
        }
        additional_data = self.extract_order_detail(html_response)
        if not additional_data:
            return
        data.update(additional_data)
        output_file = '{}/{}.json'.format(
            str(self.output_folder),
            order_id
        )
        with open(output_file, 'w', encoding='utf-8') as file_pointer:
            utils.write_json(file_pointer, data)
            print('\nJson written in {}'.format(output_file))
            print('----------------------------------------\n')

    def main(self):
        comments = []
        for index, template in enumerate(self.files):
            print(template)
            try:
                # read html file
                html_response = utils.get_html_response(template)
                file_name_only = template.split('/')[-1]
                order_match = self.order_info_pattern.findall(file_name_only)
                if order_match:
                    self.process_order_details(order_match[0], html_response)
                    continue

                match = self.thread_name_pattern.findall(file_name_only)
                if not match:
                    print('no match')
                    continue
                pid = self.thread_id = match[0]
                # pid = self.get_pid()
                final = utils.is_file_final(
                    self.thread_id, self.thread_name_pattern, self.files, index
                )
                if self.thread_id not in self.distinct_files:
                    self.distinct_files.add(self.thread_id)

                    # header data extract
                    data = self.header_data_extract(html_response, template)
                    if not data:
                        print('no data')
                        continue

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
          '//div[contains(@class, "windowbg")]'
        )
        for comment_block in comment_blocks[1:]:

            user = self.get_author(comment_block)
            authorID = self.get_author_link(comment_block)
            commentID = self.get_comment_id(comment_block)
            if not commentID:
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
                '//div[@class="windowbg"]'
            )
            if not header:
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
                    'subject': title,
                    'date': date,
                    'author': author,
                    'message': post_text.strip(),
                }
            }
        except:
            ex = traceback.format_exc()
            raise BrokenPage(ex)

    def get_date(self, tag):
        date = tag.xpath(
            'div[@class="date_post"]'
            '/div/text()'
        )
        date = date[0].strip() if date else None
        try:
            pattern = '%B %d, %Y, %I:%M:%S  %p'
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except:
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            'div[@class="post_wrapper"]/'
            'div[@class="poster"]'
            '/h4/a/text()'
        )
        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(
            'div[@class="post_wrapper"]/'
            'div[@class="postarea"]'
            '//h5/a/text()'
        )
        title = title[0].strip() if title else None
        return title

    def get_author_link(self, tag):
        author_link = tag.xpath(
            'div[@class="post_wrapper"]/'
            'div[@class="poster"]'
            '/h4/a/@href'
        )
        if author_link:
            pattern = re.compile(r'u=(\d+)')
            match = pattern.findall(author_link[0])
            author_link = match[0] if match else None
        return author_link

    def get_post_text(self, tag):
        post_text = tag.xpath(
            'div[@class="post_wrapper"]/'
            'div[@class="postarea"]'
            '//div[@class="post"]/'
            '/div[@class="inner"]/text()'
        )
        post_text = "\n".join(
            [text.strip() for text in post_text]
        ) if post_text else ""
        return post_text

    def get_comment_id(self, tag):
        commentID = ""
        comment_block = tag.xpath(
            'div[@class="date_post"]'
            '/span/text()'
        )
        if comment_block:
            comment_pattern = re.compile(r'Reply #(\d+)')
            match = comment_pattern.findall(comment_block[0])
            commentID = match[0] if match else ""
        return commentID.replace(',', '')
