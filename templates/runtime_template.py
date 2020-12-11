# -- coding: utf-8 --
import re
import dateparser

from .base_template import BaseTemplate


class RuntimeParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "runtime.rip"
        self.avatar_name_pattern = re.compile(r".*avatar_(\d+\.\w+)")
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//article[contains(@class,"post-article")]'
        self.header_xpath = '//article[contains(@class,"post-article")]'
        self.date_xpath_1 = 'div//span[contains(@class, "post_date")]/text()'
        self.date_xpath_2 = 'div//span[contains(@class, "post_date")]/span/@title'
        self.title_xpath = '//div[@class="thread-header"]/h1/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = 'div//div[@class="right postbit-number"]/strong/a/text()'

        # main function
        self.main()


    def get_author(self, tag):
        author = tag.xpath(
            './/div[contains(@class,"post-username")]/a/span/text()'
        )

        if not author:
            author = tag.xpath(
                './/div[contains(@class,"post-username")]/a/span//text()'
            )

        if not author:
            author = tag.xpath(
                './/div[contains(@class,"post-username")]/text()'
            )

        author = ''.join(author).strip() if author else None
        return author

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