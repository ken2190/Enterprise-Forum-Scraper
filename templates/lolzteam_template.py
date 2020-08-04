# -- coding: utf-8 --
import re
import traceback
import locale
import utils
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class LolzTeamParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        super().__init__(*args, **kwargs)
        self.parser_name = "lolzteam.net"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//ol[@class="messageList"]/li[contains(@id, "post-")]'
        self.header_xpath = '//ol[@class="messageList"]/li[contains(@id, "post-")]'
        self.date_xpath = 'div//span[@class="DateTime"]/@title'
        self.author_xpath = 'div//div[@class="userText"]/span/a/span/text()'
        self.title_xpath = '//div[@class="titleBar"]/h1/text()'
        self.post_text_xpath = 'div//div[@class="messageContent"]/article/blockquote/text()'
        self.avatar_xpath = 'div//div[@class="avatarHolder"]/a/span/@style'

        # main function
        self.main()

    def main(self):
        comments = []
        output_file = None
        for index, template in enumerate(self.files):
            print(template)
            try:
                html_response = utils.get_html_response(template)
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern.findall(file_name_only)
                if not match:
                    continue
                pid = self.thread_id = match[0]
                pagination = self.pagination_pattern.findall(file_name_only)
                if pagination:
                    pagination = int(pagination[0])
                final = utils.is_file_final(
                    self.thread_id, self.thread_name_pattern, self.files, index
                )
                if self.thread_id not in self.distinct_files and\
                   not output_file:

                    # header data extract
                    self.comment_index = 1
                    data = self.header_data_extract(
                        html_response,
                        template,
                    )
                    if not data or not pagination == 1:
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
            except:
                traceback.print_exc()
                continue

    def extract_comments(self, html_response):
        comments = list()
        comment_blocks = html_response.xpath(self.comments_xpath)

        if self.comment_index == 1:
            comment_blocks = comment_blocks[1:]

        for comment_block in comment_blocks:
            user = self.get_author(comment_block)
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            pid = self.thread_id
            avatar = self.get_avatar(comment_block)
            source = {
                'forum': self.parser_name,
                'pid': pid,
                'message': comment_text.strip(),
                'cid': str(self.comment_index),
                'author': user,
                'img': avatar,
            }
            if comment_date:
                source.update({
                    'date': comment_date
                })
            comments.append({
                '_source': source,
            })
            self.comment_index += 1

        return comments

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        if not date_block:
            date_block = tag.xpath(
                'div//abbr[@class="DateTime"]/text()'
            )

        date = date_block[0].strip() if date_block else ""
        try:
            pattern = "%d %b %Y в %H:%M"
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except:
            try:
                date = dparser.parse(date).timestamp()
                return str(date)
            except:
                pass

        return ""

    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if not author:
            author = tag.xpath(
                'div//div[@class="userText"]/span/a/text()')

        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = title[-1].strip() if title else None

        return title
