# -- coding: utf-8 --
import re
import utils
import datetime
import dateparser

from .base_template import BaseTemplate


class TenecParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = 'tenec.cc'
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//article[contains(@class,"cPost ipsBox")]'
        self.header_xpath = '//article[contains(@class,"cPost ipsBox")]'
        self.date_xpath = 'div//time/@datetime'
        self.author_xpath = 'aside//div[@class="name"]//strong/a//text()'
        self.title_xpath = '//h1[@class="ipsType_pageTitle ipsContained_container"]/span/span/text()'
        self.avatar_xpath = '//div[contains(@class, "cAuthorPane_photo")]/a/img/@src'
        self.avatar_ext = ''
        self.index = 0

        self.date_pattern = '%Y-%m-%dT%H:%M:%S'

        # main function
        self.main()

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = "".join([t.strip() for t in title if t.strip()])

        return title.strip().encode('latin1', errors='ignore').decode('utf8', errors='ignore')

    def get_post_text(self, tag):
        post_text_block = tag.xpath(
            'div//div[@data-role="commentContent"]'
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
        return post_text.strip().encode('latin1', errors='ignore').decode('utf8', errors='ignore')
    
    def get_author(self, tag):
        author = tag.xpath(
            'aside//a[@class="ipsType_break"]/span/span/text()'
        )
        if not author:
            author = tag.xpath(
                'aside//a[@class="ipsType_break"]/span/text()'
            )
        if not author:
            author = tag.xpath(
                'aside//a[@class="ipsType_break"]/text()'
            )
        if not author:
            author = tag.xpath(
                'aside//div[contains(@class, "lkComment_author")]/descendant::text()'
            )
        if not author:
            author = tag.xpath(
                './/h3[contains(@class, "cAuthorPane_author")]/strong/text()'
            )
        author = ' '.join(author).strip() if author else None

        return author.encode('latin1', errors='ignore').decode('utf8', errors='ignore')
    
    def get_comment_id(self, tag):
        comment_id = ""
        if self.comment_block_xpath:
            comment_block = tag.xpath(self.comment_block_xpath)
            comment_block = ''.join(comment_block)
        else:
            self.index += 1
            return str(self.index)

        if comment_block:
            comment_id = re.compile(r'(\d+)').findall(comment_block)[0]
            # comment_id = ''.join(comment_block).strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = date_block[0].strip().strip('Z') if date_block else None

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
