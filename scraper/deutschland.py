import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5

PROXY = 'http://127.0.0.1:8118'


class DeutschLandSpider(SitemapSpider):
    name = 'deutschland_spider'
    base_url = 'http://germanyruvvy2tcw.onion/'

    # Xpaths
    forum_xpath = '//a[contains(@href, "forum-")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[@class="pagination_next"]/@href'
    thread_xpath = '//tr[@class="inline_row"]'
    thread_first_page_xpath = '//span[contains(@id,"tid_")]/a/@href'
    thread_last_page_xpath = '//td[contains(@class,"forumdisplay_")]/div'\
                             '/span/span[@class="smalltext"]/a[last()]/@href'
    thread_date_xpath = '//td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/text()[1]|'\
                        '//td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/span/@title'
    thread_pagination_xpath = '//div[@class="pagination"]'\
                              '//a[@class="pagination_previous"]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//span[@class="post_date"]/text()[1]|'\
                      '//span[@class="post_date"]/span/@title'\

    topic_pattern = re.compile(
        r".*thread-(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = False
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = '%d-%m-%Y'
    post_datetime_format = '%d-%m-%Y'

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                'proxy': PROXY
            }
        )

    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip"]
            if response.meta.get(key)
        }

        meta.update(default_meta)
        meta.update({'proxy': PROXY})

        return meta

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.split(',')[0].strip()
        if not thread_date:
            return

        if any(v in thread_date.lower() for v in ['heute', 'stunde', 'minuten']):
            return datetime.today()
        elif 'gestern' in thread_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        # Standardize thread_date
        post_date = post_date.split(',')[0].strip()
        if not post_date:
            return

        if any(v in post_date.lower() for v in ['heute', 'stunde', 'minuten']):
            return datetime.today()
        elif 'gestern' in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        base_forum_url = "http://germanyruvvy2tcw.onion/forum-{}.html"
        for i in range(1, 100):
            forum_url = base_forum_url.format(i)
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)


class DeutschLandScrapper(SiteMapScrapper):

    spider_class = DeutschLandSpider
    site_name = 'deutschland_germanyruvvy2tcw'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings