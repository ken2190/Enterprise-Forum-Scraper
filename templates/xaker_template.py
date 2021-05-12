import re
import datetime
import dateparser

from .base_template import BaseTemplate


class XakerParser(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "xaker.name"
        self.avatar_name_pattern = re.compile(r".*/(\d+\.\w+)")
        self.mode = 'r'
        self.comments_xpath = '//ol[@class="messageList"]/li[contains(@class,"message")]'
        self.header_xpath = '//ol[@class="messageList"]/li[contains(@class,"message")]'
        self.date_xpath = './/span[@class="DateTime"]/@title'
        self.author_xpath = './/div[@class="userText"]/a[contains(@class,"username")]/text()|'\
                            './/div[@class="userText"]/a[contains(@class,"username")]/span/text()'
        self.post_text_xpath = './/div[contains(@class,"messageContent")]//article/blockquote/descendant::text()[not(ancestor::div[contains(@class,"bbCodeQuote")])]'
        self.avatar_xpath = './/div[contains(@class,"avatarHolder")]//img/@src'
        self.title_xpath = '//h1/text()'
        self.index = 0

        self.offset_hours = -10

        # main function
        self.main()
    
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
        date = date_block[0].strip() if date_block else None

        if not date:
            return ""

        try:
            date = float(date)
        except:
            try:
                date = dateparser.parse(date)

                if self.offset_hours:
                    date += datetime.timedelta(hours=self.offset_hours)
                date = date.timestamp()
            except Exception as err:
                err_msg = f"ERROR: Parsing {date} date is failed. {err}"
                raise ValueError(err_msg)

        curr_epoch = datetime.datetime.today().timestamp()

        if date > curr_epoch:
            err_msg = f"ERROR: the timestamp ({date}) is after current time ({curr_epoch})"
            print(err_msg)
            raise RuntimeError(err_msg)
        return str(date)
