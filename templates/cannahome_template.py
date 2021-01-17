import re
from .base_template import MarketPlaceTemplate


class CannaHomeParser(MarketPlaceTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "cannahome"
        self.list_name_xpath = '//div[contains(@class, "breadcrumb")]//a[contains(@class, "shrink")]//text()'
        self.vendor_xpath = '//div[contains(@class, "product")]//a[contains(@href, "/v/")]//text()'
        self.description_text_xpath = '//div[contains(@class, "top-tabs")]/div[contains(@class, "formatted")]//text()'
        # main function
        self.main()