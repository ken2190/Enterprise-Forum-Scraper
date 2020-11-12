# -- coding: utf-8 --
import datetime
import traceback

import dateutil.parser as dparser
import dateparser
import utils
import re

class BrokenPage(Exception):
    pass


class BaseTemplate:

    def __init__(self, *args, **kwargs):
        self.output_folder = kwargs.get('output_folder')
        self.folder_path = kwargs.get('folder_path')
        self.distinct_files = set()
        self.error_folder = f"{self.output_folder}/Errors"
        self.thread_id = None
        self.comment_pattern = None
        self.encoding = None
        self.mode = 'rb'

        self.comments_xpath = ''
        self.comment_block_xpath = ''
        self.author_xpath = ''
        self.post_text_xpath = ''
        self.protected_email_xpath = './/*[@class="__cf_email__"]/@data-cfemail'
        self.date_xpath = ''
        self.date_pattern = ''
        self.header_xpath = ''
        self.title_xpath = ''
        self.avatar_xpath = ''
        self.avatar_ext = ''
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.files = self.get_filtered_files(kwargs.get('files'))

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(x) is not None,
                files
            )
        )
        sorted_files = sorted(
            filtered_files,
            key=lambda x: (int(self.thread_name_pattern.search(x).group(1)),
                           int(self.pagination_pattern.search(x).group(1))))

        return sorted_files

    def get_html_response(self, template, pattern=None, encoding=None, mode='rb'):
        return utils.get_html_response(template, pattern, encoding, mode)

    def get_pid(self):
        return self.thread_id

    def main(self):
        comments = []
        output_file = None

        for index, template in enumerate(self.files):
            print(template)
            try:
                html_response = self.get_html_response(template, self.comment_pattern, self.encoding, self.mode)
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern.findall(file_name_only)

                if not match:
                    continue

                self.thread_id = match[0]

                pid = self.get_pid()

                pagination = None
                if getattr(self, 'pagination_pattern', None):
                    pagination = self.pagination_pattern.findall(file_name_only)
                    if pagination:
                        pagination = int(pagination[0])

                final = utils.is_file_final(
                    self.thread_id,
                    self.thread_name_pattern,
                    self.files,
                    index
                )

                if (
                    (pagination and pagination == 1) or
                    (self.thread_id not in self.distinct_files) and not output_file
                ):
                    self.distinct_files.add(self.thread_id)
                    # header data extract
                    data = self.header_data_extract(html_response, template)

                    if not data:
                        continue

                    # write file
                    output_file = '{}/{}.json'.format(
                        str(self.output_folder),
                        pid
                    )
                    file_pointer = open(output_file, 'w', encoding='utf-8')

                    utils.write_json(file_pointer, data)

                # extract comments
                comments.extend(self.extract_comments(html_response, pagination))

                if final:
                    utils.write_comments(file_pointer, comments, output_file)
                    comments = []
                    output_file = None
                    final = None

                    if getattr(self, 'index', None):
                        self.index = 1
            except BrokenPage as ex:
                utils.handle_error(
                    pid,
                    self.error_folder,
                    ex
                )
            except utils.NoAuthor as ex:
                print(ex)
                print('Aborting!!')
                return
            except Exception:
                traceback.print_exc()
                continue

    def header_data_extract(self, html_response, template):
        try:
            # ---------------extract header data ------------
            header = html_response.xpath(self.header_xpath)
            if not header:
                return

            title = self.get_title(header[0])
            date = self.get_date(header[0])
            author = self.get_author(header[0])
            post_text = self.get_post_text(header[0])
            pid = self.thread_id
            avatar = self.get_avatar(header[0])
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

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = "".join([t.strip() for t in title if t.strip()])

        return title

    def extract_comments(self, html_response, pagination=None):
        comments = list()
        comment_blocks = html_response.xpath(self.comments_xpath)

        if not self.comment_block_xpath:
            comment_blocks = comment_blocks[1:]\
                if pagination == 1 else comment_blocks

        for comment_block in comment_blocks:
            try:

                comment_id = self.get_comment_id(comment_block)
                if self.comment_block_xpath:
                    if not comment_id or comment_id == "1":
                        continue

                user = self.get_author(comment_block)
                comment_text = self.get_post_text(comment_block)
                comment_date = self.get_date(comment_block)

                pid = self.get_pid()
                avatar = self.get_avatar(comment_block)

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
            except:
                continue

        return comments

    def get_comment_id(self, tag):
        comment_id = ""
        if self.comment_block_xpath:
            comment_block = tag.xpath(self.comment_block_xpath)
            comment_block = ''.join(comment_block)
        else:
            return str(self.index)

        if comment_block:
            comment_id = re.compile(r'(\d+)').findall(comment_block)[0]
            # comment_id = ''.join(comment_block).strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')


    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if author:
            author = ''.join(author).strip()
            return author
        else:
            return ''

    def get_post_text(self, tag):
        post_text_block = tag.xpath(self.post_text_xpath)
        if not post_text_block:
            return ''
        post_text = " ".join([
            post_text.strip() for post_text in post_text_block
        ])
        protected_email = tag.xpath(self.protected_email_xpath)
        if protected_email:
            decoded_values = [
                utils.get_decoded_email(e) for e in protected_email
            ]
            for decoded_value in decoded_values:
                post_text = re.sub(
                    r'\[email.*?protected\]',
                    decoded_value,
                    post_text,
                    count=1
                )

        return post_text.strip()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = date_block[0].strip() if date_block else None

        if not date:
            return ""

        # check if date is already a timestamp
        try:
            date = dateparser.parse(date).timestamp()
            return str(date)
        except:
            try:
                date = float(date)
                return date
            except:
                try:
                    date = datetime.datetime.strptime(date, self.date_pattern).timestamp()
                    return str(date)
                except:
                    pass

        return ""

    def get_avatar(self, tag):
        avatar_block = tag.xpath(self.avatar_xpath)
        if not avatar_block:
            return ""

        if 'image/svg' in avatar_block[0]:
            return ""

        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""

        return f"{name_match[0]}.{self.avatar_ext}" if self.avatar_ext else name_match[0]


class MarketPlaceTemplate(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.thread_name_pattern = re.compile(
            r'(\w+)\.html$'
        )
        self.files = self.get_filtered_files(kwargs.get('files'))

    def main(self):
        comments = []
        output_file = None
        for index, template in enumerate(self.files):
            try:
                html_response = utils.get_html_response(template)
                pid = template.split('/')[-1].rsplit('.', 1)[0]
                pid = str(
                    int.from_bytes(
                        pid.encode('utf-8'),
                        byteorder='big'
                    ) % (10 ** 7)
                )
                self.process_page(pid, html_response)
            except BrokenPage as ex:
                utils.handle_error(
                    pid,
                    self.error_folder,
                    ex
                )
            except Exception:
                traceback.print_exc()
                continue

    def process_page(self, pid, html_response):
        data = {
            'forum': self.parser_name,
            'pid': pid
        }

        additional_data = self.extract_page_info(html_response)
        if not additional_data:
            return

        data.update(additional_data)
        final_data = {
            '_source': data
        }

        output_file = '{}/{}.json'.format(
            str(self.output_folder),
            pid
        )

        with open(output_file, 'w', encoding='utf-8') as file_pointer:
            utils.write_json(file_pointer, final_data)
            print('\nJson written in {}'.format(output_file))
            print('----------------------------------------\n')


    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(x) is not None,
                files
            )
        )

        sorted_files = sorted(
            filtered_files,
            key=lambda x: self.thread_name_pattern.search(x).group(1))

        return sorted_files


    def extract_page_info(self, html_response):
        data = dict()

        subject = self.get_title(html_response)
        author = self.get_author(html_response)
        post_text = self.get_post_text(html_response)
        avatar = self.get_avatar(html_response)

        data = {
            'subject': subject,
            'author': author,
            'message': post_text,
            'img': avatar
        }

        return data
