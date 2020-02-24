import uuid
import re

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
    base_url = "https://rstforums.com/forum/"

    # Xpath stuffs
    forum_xpath = "//h4[contains(@class,\"ipsDataItem_title\")]/a/@href|" \
                  "//ul[contains(@class,\"ipsDataItem_subList\")]/li[@class]/a/@href"
    pagination_xpath = "//li[@class=\"ipsPagination_next\"]/a/@href"

    thread_xpath = "//li[contains(@class,\"ipsDataItem\") and @data-rowid]"
    thread_first_page_xpath = "//span[contains(@class,\"ipsType_break\")]/a/@href"
    thread_last_page_xpath = "//span[contains(@class,\"ipsPagination_mini\")]/span[last()]/a/@href"
    thread_date_xpath = "//li[@class=\"ipsType_light\"]/a/time/@datetime"
    thread_pagination_xpath = "//li[@class=\"ipsPagination_prev\"]/a/@href"
    thread_page_xpath = "//li[contains(@class,\"ipsPagination_active\")]/a/text()"
    post_date_xpath = "//div[@class=\"ipsType_reset\"]/a/time/@datetime"

    avatar_xpath = "//li[@class=\"cAuthorPane_photo\"]/a/img/@src"

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    topic_pattern = re.compile(
        r"forum/topic/(\d+)-",
        re.IGNORECASE
    )

    # Other settings
    get_cookies_delay = 10
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%SZ"
    post_datetime_format = "%Y-%m-%dT%H:%M:%SZ"

    def parse(self, response):

        # Synchronize user agent for cloudfare middleware
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
                meta=self.synchronize_meta(response),
                callback=self.parse_forum
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class RSTForumsScrapper(SiteMapScrapper):
    spider_class = RSTForumsSpider


if __name__ == "__main__":
    pass
