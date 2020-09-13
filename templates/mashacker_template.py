import re
import dateparser as dparser

from .base_template import BaseTemplate


class MashackerParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "mashacker.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//li[contains(@class,"postcontainer")]'
        self.header_xpath = '//li[contains(@class,"postcontainer")]'
        self.author_xpath = './/div[contains(@class,"username_container")]//strong//text()|'\
                            './/div[contains(@class,"username_container")]/span[1]/text()'
        self.title_xpath = '//span[contains(@class,"threadtitle")]//descendant::text()'
        self.post_text_xpath = './/div[contains(@class,"postbody")]//div[@class="content"]//descendant::text()[not(ancestor::div[@class="quote_container"])]'
        self.avatar_xpath = './/div[contains(@class,"userinfo")]//a[@class="postuseravatar"]//img/@src'
        self.comment_block_xpath = './/div[contains(@class,"posthead")]//span[@class="nodecontrols"]/a//text()'
        self.date_xpath = './/span[@class="date"]//text()'
        # main function
        self.main()

    def get_date(self, tag):
        date_block = tag.xpath(
            self.date_xpath
        )
        date_block = ' '.join(date_block)
        date = date_block.strip() if date_block else ""

        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except Exception:
            return ""
        return ""
