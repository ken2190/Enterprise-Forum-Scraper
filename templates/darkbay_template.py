import re
from .base_template import MarketPlaceTemplate


class DarkbayParser(MarketPlaceTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "darkbay"
        self.list_name_xpath = '//div[contains(@class, "mt-4")]/div[@class="row"]/div[@class="col-md-5"]/h2//text()'
        self.vendor_xpath = '//div[contains(@class, "card-body")]//a[contains(@href, "/vendor/")]//text()'
        self.description_text_xpath = '//div[contains(@class, "mt-4")]/div[@class="card"]/*[not(@id="productsmenu") and not(@class="card-header1")]//text()'
        # main function
        self.main()