import re
import dateparser

from .base_template import BaseTemplate


class HackForumsParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "hackforums.net"
        self.avatar_name_pattern = re.compile(r'(\d+\.\w+)')
        self.comments_xpath = '//div[@class="post_wrapper"]'
        self.header_xpath = '//div[@class="post_wrapper"]'
        self.date_xpath_1 = 'div//span[@class="post_date"]/text()'
        self.date_xpath_2 = 'div//span[@class="post_date"]/span/@title'
        self.date_pattern = "%m-%d-%Y, %I:%M %p"
        self.title_xpath = '//td[@class="thead"]//h1/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = 'div/div[@class="post_head"]/div/strong/a/text()'
        self.author_xpath = 'div//div[@class="author_information"]/strong//text()'

        # main function
        self.main()

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