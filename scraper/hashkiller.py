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


class HashKillerSpider(SitemapSpider):
    name = "hashkiller_spider"
    
    # Url stuffs
    base_url = "https://forum.hashkiller.io"

    # Xpath stuffs
    forum_xpath = "//h3[@class=\"node-title\"]/a/@href"
    pagination_xpath = "//a[contains(@class,\"pageNav-jump--next\")]/@href"

    thread_xpath = "//div[contains(@class,\"js-threadListItem\")]"
    thread_first_page_xpath = ".//div[@class=\"structItem-title\"]"\
                              '/a[contains(@href,"threads/")]/@href'
    thread_last_page_xpath = ".//div[@class=\"structItem-minor\"]/span/"\
                             'a[contains(@href,"threads/")][last()]/@href'
    thread_date_xpath = ".//div[contains(@class,\"structItem-cell--latest\")]/a/time/@datetime"

    thread_pagination_xpath = "//a[contains(@class,\"pageNav-jump--prev\")]/@href"
    thread_page_xpath = "//li[contains(@class,\"pageNav-page--current\")]/a/text()"
    post_date_xpath = "//ul[contains(@class, 'message-attribution-main ')]//time[@datetime]/@datetime"
    avatar_xpath = "//div[@class=\"message-avatar-wrapper\"]/a/img/@src"
    use_proxy = 'On'
    
    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    topic_pattern = re.compile(
        r"threads/.*?\.(\d+)/",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*p=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    def start_requests(self):
        yield Request(
            url="https://forum.hashkiller.io/index.php",
            headers=self.headers
        )

    def parse(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", len(all_forums))

        for forum_url in all_forums:
            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url

            yield Request(
                url=forum_url,
                headers=self.headers,
                meta=self.synchronize_meta(response),
                callback=self.parse_forum
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class HashKillerScrapper(SiteMapScrapper):
    spider_class = HashKillerSpider
    site_type = 'forum'


if __name__ == "__main__":
    pass
