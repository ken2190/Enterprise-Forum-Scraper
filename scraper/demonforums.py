import time
import requests
import os
import json
import re
import scrapy
from math import ceil
from copy import deepcopy
from urllib.parse import urlencode
import configparser
from scrapy.http import Request, FormRequest
from lxml.html import fromstring
from scrapy.crawler import CrawlerProcess
from scraper.base_scrapper import BypassCloudfareNoProxySpider, SiteMapScrapper


REQUEST_DELAY = 0.3
NO_OF_THREADS = 3


class DemonForumsSpider(BypassCloudfareNoProxySpider):
    name = 'demonforums_spider'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_url = 'https://demonforums.net/'
        self.headers = {
            'Referer': 'https://demonforums.net/',
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.parse,
            meta={
                "cookiejar": "123123"
            }
        )

    def parse(self, response):

        self.logger.info(
            "Succesfully bypass cloudfare."
        )

        return


class DemonForumsScrapper(SiteMapScrapper):

    spider_class = DemonForumsSpider

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
