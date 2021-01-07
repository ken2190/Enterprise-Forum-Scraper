import re
from .base_template import MarketPlaceTemplate


class TorrezParser(MarketPlaceTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "torrez"
        self.list_name_xpath = '//div[contains(@class, "titleHeader")]/h3//text()'
        self.vendor_xpath = '//div[contains(@class, "singleItemDetails")]//a[contains(@href, "/profile/")]//text()'
        self.description_text_xpath = '//div[contains(@class, "tab-content")]/div[contains(@class, "active")]//text()'
        # main function
        self.main()