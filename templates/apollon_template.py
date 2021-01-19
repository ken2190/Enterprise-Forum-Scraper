import re
from .base_template import MarketPlaceTemplate


class ApollonParser(MarketPlaceTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "apollon"
        self.list_name_xpath = '//div[contains(@class, "table-responsive")]//a[contains(@href, "ls_id")]//text()'
        self.vendor_xpath = '//div[contains(@class, "table-responsive")]//div[@align="left"]//a[contains(@href, "user.php")]//text()'
        self.description_text_xpath = '//div[contains(@class, "active")]//div[contains(@class, "panel-body")]//text()'
        # main function
        self.main()

    def get_vendor(self, html_response):
        vendor = html_response.xpath(self.vendor_xpath)
        if vendor:
            vendor = ''.join(vendor).strip()
            if " (" in vendor:
                vendor = vendor.split(" (")[0]
            return vendor
        else:
            return ''