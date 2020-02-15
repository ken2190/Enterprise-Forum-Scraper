import re

from datetime import datetime

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = .3
NO_OF_THREADS = 12
USERNAME = "night_cyrax"
PASSWORD = "a63ffcb44e1a11eaa087b42e994a598f"


class VoidToSpider(SitemapSpider):

    name = "void_to"

    # Url stuffs
    base_url = "https://void.to/"
    login_url = "https://void.to/member.php?action=login"

    # Css stuffs
    login_form_css = "form[action=\"member.php\"]"

    # Xpath stuffs
    recaptcha_site_key_xpath = "//div[@class=\"g-recaptcha\"]/@data-sitekey"

    # Other settings
    use_proxy = False

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        yield Request(
            url=self.login_url,
            headers=self.headers,
            callback=self.parse_login,
            meta=self.synchronize_meta(response)
        )

    def parse_login(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response,
            formcss=self.login_form_css,
            formdata={
                "username": USERNAME,
                "password": PASSWORD,
                "remember": "yes",
                "submit": "Login",
                "action": "do_login",
                "url": "",
                "g-recaptcha-response": self.solve_recaptcha(response)
            },
            meta=self.synchronize_meta(response),
            dont_filter=True,
            headers=self.headers,
            callback=self.parse_start
        )

    def parse_start(self, response):
        self.logger.info(
            response.text
        )


class VoidToScrapper(SiteMapScrapper):

    spider_class = VoidToSpider

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "DOWNLOAD_DELAY": REQUEST_DELAY,
                "CONCURRENT_REQUESTS": NO_OF_THREADS,
                "CONCURRENT_REQUESTS_PER_DOMAIN": NO_OF_THREADS,
            }
        )
        return settings


if __name__ == '__main__':
    pass
