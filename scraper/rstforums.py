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

    def parse(self, response):
        pass


class RSTForumsScrapper(SiteMapScrapper):

    spider_class = RSTForumsSpider


if __name__ == "__main__":
    pass
