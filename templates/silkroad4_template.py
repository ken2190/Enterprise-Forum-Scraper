import re
from .base_template import MarketPlaceTemplate


class SilkRoad4Parser(MarketPlaceTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "silkroad4"
        self.list_name_xpath = '//h3[@align="center"]/text()'
        self.vendor_xpath = user_xpath = '//a[contains(text(), "View Listings")]'\
                 '/following-sibling::a[contains(@href, "profile=")][1]/text()'
        self.description_text_xpath = '(//div[@id="cats"])[2]//text()'
        # main function
        self.main()
