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

USER = "thecreator101@protonmail.com"
PASS = "Night#Phreaker"


class PhreakerSpider(SitemapSpider):

    name = "phreaker_spider"

    # Url stuffs
    base_url = "https://phreaker.pro"

    # Xpath stuffs
    forum_xpath = "//h3[@class=\"node-title\"]/a/@href"
    pagination_xpath = "//a[contains(@class,\"pageNav-jump--next\")]/@href"

    thread_xpath = "//div[contains(@class,\"structItem--thread\")]"
    thread_first_page_xpath = ".//div[@class=\"structItem-title\"]/a[@id]/@href"
    thread_last_page_xpath = ".//span[@class=\"structItem-pageJump\"]/a[last()]/@href"
    thread_date_xpath = ".//time[@class=\"structItem-latestDate u-dt\"]/@datetime"
    thread_pagination_xpath = "//a[contains(@class,\"pageNav-jump--prev\")]/@href"
    thread_page_xpath = "//li[contains(@class,\"pageNav-page--current\")]/a/text()"

    post_date_xpath = "//time[@class=\"u-dt\"]/@datetime"
    avatar_xpath = "//div[@class=\"message-avatar-wrapper\"]/a/img/@src"

    # Regex stuffs
    topic_pattern = re.compile(
        r"(?<=\.)\d*?(?=\/)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    def parse_thread_date(self, thread_date):
        return super().parse_thread_date(thread_date[:-5])

    def parse_post_date(self, post_date):
        return super().parse_post_date(post_date[:-5])

    def parse(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", len(all_forums))
        for forum_url in all_forums:
            # Standardize forum url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url

            yield Request(
                url=forum_url,
                headers=self.headers,
                meta=self.synchronize_meta(response),
                callback=self.parse_forum
            )

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class PhreakerScrapper(SiteMapScrapper):
    spider_class = PhreakerSpider
    site_type = 'forum'
