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


class ScrapeBoxForumSpider(SitemapSpider):
    name = "scrapeboxforum_spider"
    
    # Url stuffs
    base_url = "https://scrapeboxforum.com/"

    # Xpath stuffs
    forum_xpath = "//td[contains(@class,\"trow\")]/strong/a/@href"
    pagination_xpath = "//a[@class=\"pagination_next\"]/@href"

    thread_xpath = "//tr[@class=\"inline_row\"]"
    thread_first_page_xpath = "//span[contains(@id,\"tid\")]/a/@href"
    thread_last_page_xpath = "//span[contains(@id,\"tid\")]/following-sibling::span/a[last()]/@href"
    thread_date_xpath = "//span[@class=\"lastpost smalltext\"]/text()[contains(.,\"-\")]|" \
                        "//span[@class=\"lastpost smalltext\"]/span[@title]/@title"

    thread_pagination_xpath = "//a[@class=\"pagination_previous\"]/@href"
    thread_page_xpath = "//span[@class=\"pagination_current\"]/text()"
    post_date_xpath = "//span[@class=\"post_date\"]/text()[contains(.,\"-\")]|" \
                      "//span[@class=\"post_date\"]/span[@title]/@title"
    avatar_xpath = "//div[@class=\"author_avatar\"]/a/img/@src"
    
    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    sitemap_datetime_format = "%m-%d-%Y"
    post_datetime_format = "%m-%d-%Y"

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        return datetime.strptime(
            thread_date.strip()[:10],
            self.sitemap_datetime_format
        )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        return datetime.strptime(
            post_date.strip()[:10],
            self.post_datetime_format
        )

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


class ScrapeBoxForumScrapper(SiteMapScrapper):

    spider_class = ScrapeBoxForumSpider


if __name__ == "__main__":
    pass
