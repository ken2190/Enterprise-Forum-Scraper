import re
from .base_template import MarketPlaceTemplate


class DarkFoxParser(MarketPlaceTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "darkfox"
        self.list_name_xpath = '//h1[contains(@class, "title")]//text()'
        self.vendor_xpath = '//h3[contains(., "Vendor:")]/a/text()'
        self.description_text_xpath = '//div[contains(@class, "box grey")]//text()'
        # main function
        self.main()
