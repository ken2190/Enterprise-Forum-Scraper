# -- coding: utf-8 --
import re
import traceback
import datetime
import utils

from .base_template import BaseTemplate


class KickAssParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "kickass"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html'
        )
        self.uid_pattern = re.compile(
            r'UID-(\d+)\.html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[contains(@class,"post classic")]'
        self.header_xpath = '//div[contains(@class,"post classic")]'
        self.date_pattern = '%Y-%m-%d %H:%M:%S'
        self.date_xpath = 'div//span[@class="post-link"]/a/text()'
        self.author_xpath = 'div//div[@class="author_information"]//a/span/strong/text()'
        self.title_xpath = '//span[@class="active"]/text()'
        self.post_text_xpath = 'div[@class="post_content"]/div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = 'div[@class="post_content"]//strong/a/text()'

        # main function
        self.main()

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
            except Exception:
                traceback.print_exc()
                continue

    def get_avatar(self, tag):
        avatar_block = tag.xpath(self.avatar_xpath)
        if not avatar_block:
            return ""
        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""
        return name_match[0] if 'svg' not in name_match[0] else ''
