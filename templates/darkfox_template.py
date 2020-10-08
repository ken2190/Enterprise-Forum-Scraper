import re
from .base_template import MarketPlaceTemplate


class DarkFoxParser(MarketPlaceTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "darkfox"
        self.thread_name_pattern = re.compile(
            r'(\w+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.avatar_xpath = './/img[@class="slide-main"]/@src'
        self.title_xpath = '//h1[contains(@class,"title")]/text()'
        self.author_xpath = '//h3/a[contains(@href,"/user/")]/text()'
        self.post_text_xpath = '//div[@class="pre-line"]/descendant::text()'
        # main function
        self.main()
