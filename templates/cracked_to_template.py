# -- coding: utf-8 --
import re
import utils
import dateparser

from .base_template import BaseTemplate


class CrackedToParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "cracked.to"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//div[contains(@class, "post-box")]'
        self.header_xpath = '//div[contains(@class, "post-box")]'
        self.date_xpath_1 = './/span[@class="post_date"]/text()'
        self.date_xpath_2 = './/span[@class="post_date"]/span/@title'
        self.date_pattern = "%H:%M %p - %d %B, %Y"
        self.title_xpath = '//div[@class="thread-header"]/h1/text()'
        self.comment_block_xpath = './/span[contains(@class, "posturl")]//strong/a/text()|'\
            './/div[contains(@class,"post_body")]/descendant::text()'
        self.comment_id_xpath = './/div[contains(@class, "postbit-number")]//text()'
        self.avatar_xpath = './/div[@class="post-avatar"]//a/img/@src'
        self.author_xpath = './/div[contains(@class,"post-username")]//text()'
        # main function
        self.main()

    def get_post_text(self, tag):
        post_text_block = tag.xpath(
            './/div[starts-with(@id, "pid_")]/text()'
        )
        protected_email = tag.xpath(
            './/div//div[@class="post_body scaleimages"]/'
            'descendant::*[@class="__cf_email__"]/@data-cfemail'
        )

        post_text = " ".join([
            post_text.strip() for post_text in post_text_block
        ])

        if protected_email:
            decoded_values = [utils.get_decoded_email(e) for e in protected_email]
            for decoded_value in decoded_values:
                post_text = re.sub(
                    r'\[email.*?protected\]',
                    decoded_value,
                    post_text,
                    count=1
                )

        return post_text.strip()

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath_1)
        date = date_block[0].strip() if date_block else None

        if not date:
            date_block = tag.xpath(self.date_xpath_2)
            date = date_block[0].strip() if date_block else None

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

    def get_comment_id(self, tag):
        comment_id = ""
        if self.comment_id_xpath:
            comment_block = tag.xpath(self.comment_id_xpath)
            comment_block = ''.join(comment_block)
        else:
            return str(self.index)

        if comment_block:
            comment_id = re.compile(r'(\d+)').findall(comment_block)[0]
            # comment_id = ''.join(comment_block).strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')