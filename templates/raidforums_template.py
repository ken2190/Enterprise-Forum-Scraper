# -- coding: utf-8 --
import re
import utils

from .base_template import BaseTemplate


class RaidForumsParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "raidforums.com"
        self.avatar_name_pattern = re.compile(r'(\d+\.\w+)')
        self.comments_xpath = '//div[@id="posts"]/div[contains(@class,"post")]'
        self.header_xpath = '//div[@id="posts"]/div[contains(@class,"post")]'
        self.date_xpath = './/div//span[@class="post_date"]/text()|' \
                          './/div//span[@class="post_date"]/span/@title'
        self.author_xpath = './/div//div[contains(@class,"post__user-profile")]/a/@href|' \
                            './/div//div[contains(@class,"post__user-profile")]/text()'
        self.title_xpath = '//span[@class="thread-info__name rounded"]/text()'
        self.post_text_xpath = './/div//div[@class="post_body scaleimages"]' \
                               '//descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = './/div//a[@class="post__user-avatar"]/img/@src'
        self.comment_block_xpath = './/div//div[@class="post_head"]//a/text()'
        self.offset_hours = -1
        self.date_pattern = "%B %d, %Y at %I:%M %p"
        # main function
        self.main()

    def get_post_text(self, tag):
        post_text = tag.xpath(self.post_text_xpath)
        protected_email = tag.xpath(
            'div//div[@class="post_body scaleimages"]/'
            'descendant::*[@class="__cf_email__"]/@data-cfemail'
        )
        post_text = "\n".join(
            [text.strip() for text in post_text]
        ) if post_text else ""

        if protected_email:
            decoded_values = [utils.get_decoded_email(e) for e in protected_email]
            for decoded_value in decoded_values:
                post_text = re.sub(
                    r'\[email.*?protected\]',
                    decoded_value,
                    post_text,
                    count=1
                )

        return post_text

    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if author:
            author = ''.join(author).strip()
            author = author.split('User-')[-1]
            return author
        else:
            return ''

    def construct_date_string(self, date_block):
        if not date_block:  # if xpaths don't match return empty string.
            return None
        if ':' in date_block[0]:  # if title has complete date with time. return it as is.
            return date_block[0].strip()
        else:  # if title does not have time in it, grabs it from span text and append it.
            return ''.join(date_block).strip()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date_str = self.construct_date_string(date_block)
        date = self.parse_date_string(date_str)
        return date
