import uuid

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


class RSTForumsSpider(SitemapSpider):
    name = "rstforums_spider"

    # Url stuffs
    base_url = "https://rstforums.com/"

    # Xpath stuffs

    # Regex stuffs

    # Other settings
    get_cookies_delay = 10

    def start_requests(self):
        """
        :return: => request start urls if no sitemap url or no start date
                 => request sitemap url if sitemap url and start date
        """

        # Load cookies
        cookies, ip = self.get_cookies(proxy=self.use_proxy)

        yield Request(
            url=self.base_url,
            headers=self.headers,
            dont_filter=True,
            cookies=cookies,
            meta={
                "cookiejar": uuid.uuid1().hex,
                "ip": ip
            }
        )

    def parse(self, response):
        with open(
            file="response.html",
            mode="w+",
            encoding="utf-8"
        ) as file:
            file.write(response.text)


class RSTForumsScrapper(SiteMapScrapper):

    spider_class = RSTForumsSpider


if __name__ == "__main__":
    pass
