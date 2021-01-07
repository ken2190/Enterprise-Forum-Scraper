import re
from .base_template import MarketPlaceTemplate


class CannaZoneParser(MarketPlaceTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "cannazone"
        self.list_name_xpath = '(//div[contains(@class, "product-information")])[1]/h2/text()'
        self.vendor_xpath = '//div[contains(@class, "product-information-vendor")]//a[contains(@class, "vendor_rating")]/text()'
        self.description_text_xpath = '(//div[contains(@class, "product-details")]//div[contains(@class, "content")])[1]//text()'
        # main function
        self.main()