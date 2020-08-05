import re

from .base_template import BaseTemplate


class BMRParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "black market reloaded"
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.thread_name_pattern = re.compile(r'(viewtopic\.php.*id=\d+)')
        self.comments_xpath = '//div[contains(@class, "replypost")]'
        self.header_xpath = '//div[@class="main-content main-topic"]/div[contains(@class,"firstpost")]'
        self.date_xpath = 'div//span[@class="post-link"]/a/text()'
        self.date_pattern = '%Y-%m-%d %H:%M'
        self.author_xpath = 'div//span[@class="post-byline"]/em/a/text()'
        self.title_xpath = '//h1[@class="main-title"]/a/text()'
        self.post_text_xpath = 'div//div[@class="entry-content"]/*'
        self.comment_block_xpath = 'div//span[@class="post-num"]/text()'

        # main function
        self.main()

    def get_filtered_files(self, files):
        final_files = list()
        for file in files:
            file_name_only = file.split('/')[-1]
            if file_name_only.startswith('viewtopic.php'):
                final_files.append(file)

        return sorted(final_files)

    def extract_comments(self, html_response, pagination):
        comments = list()
        comment_blocks = html_response.xpath(self.comments_xpath)

        for comment_block in comment_blocks[1:]:
            commentID = self.get_comment_id(comment_block)
            if not commentID:
                continue

            user = self.get_author(comment_block)
            authorID = self.get_author_link(comment_block)
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            comments.append({
                '_source': {
                    'pid': self.thread_id.split('id=')[-1],
                    'date': comment_date,
                    'message': comment_text.strip(),
                    'cid': commentID,
                    'author': user,
                },
            })

        return comments

    def get_post_text(self, tag):
        post_text = None
        post_text_block = tag.xpath(self.post_text_xpath)
        post_text = "\n".join([
            post_text.xpath('string()') for post_text in post_text_block
        ])

        return post_text
