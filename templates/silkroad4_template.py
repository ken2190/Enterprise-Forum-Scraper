import re
from .base_template import MarketPlaceTemplate


class SilkRoad4Parser(MarketPlaceTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "silkroad4"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.avatar_xpath = './/div[@id="img"]/img/@src'
        self.title_xpath = '//h3/text()'
        self.author_xpath = '//div[@id="cats"]/div/a[2]/text()'
        self.post_text_xpath = '//div[@id="cats"][2]/div/descendant::text()'
        # main function
        self.main()

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = "".join([t.strip() for t in title if t.strip()])
        return title.split('Place')[0] if title else ''
