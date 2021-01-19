import re
from .base_template import MarketPlaceTemplate


class TorParser(MarketPlaceTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "tor"
        self.list_name_xpath = '//div[contains(@class, "main")]/h3//text()'
        self.vendor_xpath = '//div[contains(@class, "media-body")]//a[contains(@href, "/profiles/")]//text()'
        self.description_text_xpath = '(//div[contains(@class, "main")]//div[contains(@class, "panel-body")])[1]//text()'
        # main function
        self.main()