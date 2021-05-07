# -- coding: utf-8 --
import re
import utils
import datetime
import dateparser

from .base_template import BaseTemplate


class ScrapeBoxForumParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "scrapeboxforum.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@class="post "]'
        self.header_xpath = '//div[@class="post "]'
        self.date_xpath = 'div//span[@class="post_date"]//text()[' \
                          'not(parent::span[@class="post_edit"]' \
                          '|parent::span[@class="edited_post"]' \
                          '|parent::a)]'
        self.date_pattern = "%m-%d-%Y, %I:%M %p"
        self.title_xpath = '//td[@class="thead"]/div/strong/text()'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = 'div/div[@class="post_head"]/div/strong/a/text()'

        # main function
        self.main()

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(
                    x.split('/')[-1]) is not None,
                files
            )
        )
        sorted_files = sorted(
            filtered_files,
            key=lambda x: int(self.thread_name_pattern.search(
                x.split('/')[-1]).group(1)))

        return sorted_files

    def get_author(self, tag):
        author = tag.xpath(
            'div//div[@class="author_information"]/strong/span/a/text()'
        )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]/strong//em/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]/strong//b/span/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]'
                '/strong/span/a/span/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]'
                '/strong/span/a/span/strong/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]'
                '/strong/span/a/span/bold/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]'
                '/strong/span/a/span/strong/s/text()'
            )

        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = title[-1].strip() if title else None

        return title

    def get_post_text(self, tag):
        post_text_block = tag.xpath(
            'div//div[@class="post_body scaleimages"]'
            '/descendant::text()[not(ancestor::blockquote)]'
        )
        protected_email = tag.xpath(
            'div//div[@class="post_body scaleimages"]/'
            'descendant::*[@class="__cf_email__"]/@data-cfemail'
        )
        post_text = "".join([
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
        date_block = tag.xpath(self.date_xpath)
        date = ''.join(date_block).strip() if date_block else None

        if not date:
            return ""

        # check if date is already a timestamp
        try:
            date = datetime.datetime.strptime(date, self.date_pattern).timestamp()
        except:
            try:
                date = float(date)
            except:
                msg = f"WARN: could not figure out date from: ({date}) " \
                      f"using date pattern ({self.date_pattern}). So, try to parse" \
                      f"using auto parsing library."
                print(msg)
                try:
                    date = dateparser.parse(date).timestamp()
                except Exception as err:
                    err_msg = f"ERROR: Parsing {date} date is failed. {err}"
                    raise ValueError(err_msg)

        curr_epoch = datetime.datetime.today().timestamp()

        if date > curr_epoch:
            err_msg = f"ERROR: the timestamp ({date}) is after current time ({curr_epoch})"
            print(err_msg)
            raise RuntimeError(err_msg)
        return str(date)
