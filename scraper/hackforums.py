import time
import requests
import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

REQUEST_DELAY = 0.1
NO_OF_THREADS = 16
USERNAME = ""
PASSWORD = ""


class HackForumsSpider(SitemapSpider):
    name = "hackforums_spider"

    # Url stuffs
    base_url = "https://hackforums.net/"

    # Xpath stuffs
    forum_xpath = "//a[contains(@href,\"forumdisplay.php\")]/@href"
    pagination_xpath = "//a[@class=\"pagination_next\"]/@href"

    thread_xpath = "//tr[@class=\"inline_row\"]"
    thread_first_page_xpath = "//span[contains(@id,\"tid\")]/a/@href"
    thread_last_page_xpath = "//span[@class=\"smalltext\" and contains(text(),\"Pages:\")]/a[last()]/@href"
    thread_date_xpath = "//span[@class=\"lastpost smalltext\"]/text()[contains(.,\"-\")]|" \
                        "//span[@class=\"lastpost smalltext\"]/span[@title]/@title"

    thread_page_xpath = None  # Xpath of current page button in thread detail #
    thread_pagination_xpath = None  # Xpath of previous button in thread pagination #

    # Regex stuffs
    topic_pattern = re.compile(
        r"tid=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    sitemap_datetime_format = "%m-%d-%Y, %I:%M %p"
    post_datetime_format = "%m-%d-%Y, %I:%M %p"

    def parse(self, response):

        # Synchronize user agent for cloudfare middlewares
        self.synchronize_headers(response)

        # Load all forums
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


class HackForumsScrapper(SiteMapScrapper):
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


if __name__ == "__main__":
    pass
