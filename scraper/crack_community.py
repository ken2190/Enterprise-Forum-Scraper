import os
import re
import scrapy
import uuid

from scrapy.http import Request, FormRequest
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 0.3
NO_OF_THREADS = 3


class CrackCommunitySpider(SitemapSpider):
    
    name = "crackcommunity_spider"
    
    # Url stuffs
    base_url = "http://crackcommunity.com/"

    # Regex pattern
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    topic_pattern = re.compile(
        r"threads/.*\.(\d+)/",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page-(\d+)",
        re.IGNORECASE
    )

    handle_httpstatus_list = [503]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "Host": "crackcommunity.com"
            }
        )

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                "cookiejar": uuid.uuid1().hex
            }
        )

    def parse(self, response):
        self.logger.info(
            response.text
        )


class CrackCommunityScrapper(SiteMapScrapper):

    spider_class = CrackCommunitySpider
    site_name = 'crackcommunity.com'

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
            }
        )
        return spider_settings
