import os
import re

from datetime import (
    datetime,
    timedelta
)
from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)
USER = "cyrax"
PASS = "Night#Xss007"
REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class XSSSpider(SitemapSpider):
    name = "xss_spider"

    # Url stuffs
    base_url = "https://xss.is"

    # Regex stuffs
    topic_pattern = re.compile(
        r"threads/(\d+)/$",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page-(\d+)$",
        re.IGNORECASE
    )
    
    # Xpath stuffs
    forum_xpath = "//h3[@class=\"node-title\"]/a/@href"
    thread_xpath = "//div[contains(@class,\"structItem--thread\")]"
    thread_first_page_xpath = "//div[contains(@class,\"structItem-title\")]/" \
                              "a[contains(@href,\"threads/\")]/@href"
    thread_last_page_xpath = "//span[contains(@class,\"structItem-pageJump\")]/" \
                             "a[contains(@href,\"threads/\") and last()]/@href"
    thread_date_xpath = "//time[contains(@class,\"structItem-latestDate\")]/@datetime"

    pagination_xpath = "//a[contains(@class,\"pageNav-jump--next\")]/@href"
    thread_pagination_xpath = "//div[contains(@class,\"pageNav \")]/a[contains(@class,\"prev\")]/@href"
    thread_page_xpath = "//li[contains(@class,\"pageNav-page--current\")]/a/text()"
    post_date_xpath = "//div[@class=\"message-attribution-main\"]/a/time/@datetime"
    avatar_xpath = "//div[contains(@class,\"message-avatar\")]/div/a/img/@src"

    # Other settings
    use_proxy = False
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        return datetime.strptime(
            thread_date.strip()[:-5],
            self.sitemap_datetime_format
        )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        return datetime.strptime(
            post_date.strip()[:-5],
            self.post_datetime_format
        )

    def parse(self, response):

        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        
        # Login stuffs
        token = response.xpath(
            "//input[@name=\"_xfToken\"]/@value"
        ).extract_first()
        params = {
            "login": USER,
            "password": PASS,
            "remember": "1",
            "_xfRedirect": "https://xss.is/",
            "_xfToken": token
        }
        yield FormRequest(
            url="https://xss.is/login/login",
            callback=self.parse_start,
            formdata=params,
            headers=self.headers,
            meta=self.synchronize_meta(response),
            dont_filter=True,
        )

    def parse_start(self, response):

        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url

            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class XSSScrapper(SiteMapScrapper):

    spider_class = XSSSpider

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
                'HTTPERROR_ALLOWED_CODES': [403]
            }
        )
        return settings
