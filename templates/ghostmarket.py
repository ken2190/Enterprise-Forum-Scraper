# -- coding: utf-8 --
import re
import utils
import datetime
import traceback
import dateparser

from .base_template import BrokenPage
from .base_template import BaseTemplate


class GhostmarketParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        super().__init__(*args, **kwargs)
        self.parser_name = "ghostmarket.net"
        self.thread_name_pattern = re.compile(
            r'viewtopic\.php(?!.*\d+p\d+.htm$)(\w+?)(start\d+)?\.htm$'
        )
        self.pagination_pattern = re.compile(
            r'viewtopic.*?\d+start(\d+)\.htm$'
        )

        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="page-body"]/div[contains(@class, "post")]'
        self.header_xpath = '//div[@id="page-body"]/div[contains(@class, "post")]'
        self.date_xpath = './/div[@class="postbody"]//p[@class="author"]//text()'
        self.author_xpath = './/dl[@class="postprofile"]//dt//a//text()'
        self.title_xpath = '//div[@id="page-body"]/h2/a/text()'
        self.post_text_xpath = './/div[@class="content"]//text()'
        self.avatar_xpath = './/dl[@class="postprofile"]//dt//a//img[@alt="User avatar"]/@src'
        self.index = 1

        # main function
        self.main()

    @staticmethod
    def get_hashed_id(pid):
        hashed_id = str(
            int.from_bytes(
                pid.encode('utf-8'),
                byteorder='big'
            ) % (10 ** 10)
        )

        return hashed_id

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(x) is not None,
                files
            )
        )
        sorted_files = sorted(
            filtered_files,
            key=lambda x: (
                int(GhostmarketParser.get_hashed_id(self.thread_name_pattern.search(x).group(1))),
                int(self.pagination_pattern.search(x).group(1)) if self.pagination_pattern.search(x) else 1
            )
        )
        return sorted_files

    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)

        if author:
            author = ''.join(author).strip().split('\n')[0].strip()
            return author
        else:
            return ''

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = ''.join(date_block).strip() if date_block else None
        date = date.split('»')[-1]

        if not date:
            return ""

        try:
            date = datetime.datetime.strptime(date, self.date_pattern).timestamp()
        except:
            try:
                date = dateparser.parse(date).timestamp()
            except:
                date = ""

        return date

    def main(self):
        comments = []
        output_file = None

        for index, template in enumerate(self.files):
            try:
                print(template)
                html_response = self.get_html_response(template,
                                                       self.comment_pattern,
                                                       self.encoding,
                                                       self.mode)
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern.findall(file_name_only)

                if not match:
                    continue

                self.thread_id = self.get_hashed_id(match[0][0])
                pid = self.get_pid()

                pagination = None

                if getattr(self, 'pagination_pattern', None):
                    pagination = self.pagination_pattern.findall(file_name_only)
                    if pagination:
                        pagination = int(pagination[0])

                final = utils.is_file_final(
                    match[0],
                    self.thread_name_pattern,
                    self.files,
                    index
                )

                if (
                        (pagination and pagination == 1) or
                        (self.thread_id not in self.distinct_files) and
                        not output_file
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

                    error_msg = utils.write_json(file_pointer, data, self.start_date, self.checkonly)
                    if error_msg:
                        print(error_msg)
                        print('----------------------------------------\n')
                        if self.missing_header_file_limit > 0:
                            utils.handle_missing_header(
                                template,
                                self.missing_header_folder
                            )
                            self.missing_header_file_limit -= 1
                        else:
                            print("----------------------------------\n")
                            print("Found 50 Files with missing header or date")
                            break
                        continue
                # extract comments
                extracted = self.extract_comments(html_response, pagination)
                comments.extend(extracted)

                # missing author and date check
                if self.checkonly:
                    error_msg = ""
                    for row in extracted:
                        if not row['_source'].get('author'):
                            error_msg = f'ERROR: Null Author Detected. pid={row["_source"]["pid"]};'
                            if row['_source'].get('cid'):
                                error_msg += f' cid={row["_source"]["cid"]};'
                        elif not row['_source'].get('date'):
                            error_msg = f'ERROR: Date not present. pid={row["_source"]["pid"]};'
                            if row['_source'].get('cid'):
                                error_msg += f' cid={row["_source"]["cid"]};'
                        if error_msg:
                            break
                    if error_msg:
                        print(error_msg)
                        print('----------------------------------------\n')
                        if self.missing_header_file_limit > 0:
                            utils.handle_missing_header(
                                template,
                                self.missing_header_folder
                            )
                            self.missing_header_file_limit -= 1
                        else:
                            print("----------------------------------\n")
                            print("Found 50 Files with missing header or date")
                            break

                if final:
                    utils.write_comments(file_pointer, comments, output_file, self.start_date)
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
            except Exception:
                traceback.print_exc()
                continue
