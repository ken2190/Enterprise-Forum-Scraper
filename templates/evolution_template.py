import re
import traceback
import utils
from lxml.html import fromstring

from .base_template import BaseTemplate


class EvolutionParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "evolution marketplace"
        self.thread_name_pattern = re.compile(r'viewtopic\.php.*id=(\d+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="brdmain"]/div[@id and @id!="quickpost"]'
        self.header_xpath = '//div[@id="brdmain"]/div[contains(@class,"blockpost1")]'
        self.date_xpath = 'h2/span/a/text()'
        self.date_pattern = '%Y-%m-%d %H:%M:%S'
        self.title_xpath = '//div[@class="postright"]/h3/text()'
        self.post_text_xpath = 'div//div[@class="postmsg"]/*'
        self.comment_block_xpath = 'h2/span/span/text()'

        # main function
        self.main()

    def get_html_response(self, file):
        with open(file, 'rb') as f:
            content = str(f.read())
            content = content.split('SAMEORIGIN')[-1]
            content = content.replace('\\r', '')\
                             .replace('\\n', '')\
                             .replace('\\t', '')\
                             .strip()
            html_response = fromstring(content)
            return html_response

    def main(self):
        comments = []
        for index, template in enumerate(self.files):
            print(template)
            try:
                # read html file
                if template.endswith('.txt'):
                    html_response = self.get_html_response(template)
                else:
                    html_response = utils.get_html_response(template)
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern.findall(file_name_only)
                if not match:
                    continue
                pid = self.thread_id = match[0]
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
        comment_blocks = html_response.xpath(self.comments_xpath)

        for comment_block in comment_blocks[1:]:
            user = self.get_author(comment_block)
            commentID = self.get_comment_id(comment_block)
            if not commentID:
                continue

            pid = self.thread_id
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            source = {
                'forum': self.parser_name,
                'pid': pid,
                'message': comment_text.strip(),
                'cid': commentID,
                'author': user,
            }
            if comment_date:
                source.update({
                    'date': comment_date
                })

            comments.append({
                '_source': source,
            })

        return comments

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

        if not author:
            author = tag.xpath(
                'div[@class="box"]//dt/strong/'
                '/a/text()'
            )

        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = title[0].replace('Re:', '').strip() if title else None

        return title

    def get_post_text(self, tag):
        post_text = None
        post_text_block = tag.xpath(self.post_text_xpath)
        post_text = "\n".join([
            post_text.xpath('string()') for post_text in post_text_block
        ])

        return post_text

    def get_avatar(self, tag):
        pass
