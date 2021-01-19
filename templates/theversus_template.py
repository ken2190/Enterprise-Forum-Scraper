import re
from .base_template import MarketPlaceTemplate


class TheVersusParser(MarketPlaceTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "theversus"
        self.list_name_xpath = '//div[contains(@class, "listing__title")]//text()'
        self.vendor_xpath = '//div[contains(@class, "listing__vendor")]//a[contains(@href, "/user/")]//text()'
        self.description_text_xpath = '(//div[@class="tabs__content"])[1]//text()'
        # main function
        self.main()
