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


class HoxForumSpider(SitemapSpider):
    name = "hoxforum_spider"

    # Url stuffs
    base_url = "http://www.hoxforum.com/"

    # Xpath stuffs
    forum_xpath = '//div[contains(@class,"trow")]//h4/a/@href'
    pagination_xpath = '//a[@class="pagination_next"]/@href'

    thread_xpath = '//div[contains(@class,"inline_row")]'
    thread_first_page_xpath = '//span[contains(@id,"tid")]/a/@href'
    thread_last_page_xpath = '//div[@class="smalltext"]/span[contains(@class, "smalltext")]/a[last()]/@href'
    thread_date_xpath = '//div[@class="threadbit_lastpost smalltext"]/span/text()[last()]'

    thread_pagination_xpath = '//div[@class="pagination"]/a[@class="pagination_previous"]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//span[@class="post_date"]/text()'

    avatar_xpath = '//div[contains(@class, "author_avatar")]/a/img/@src'

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
    sitemap_datetime_format = "%m-%d-%Y, %I:%M %p"
    post_datetime_format = "%m-%d-%Y, %I:%M %p"

    def parse_thread_date(self, thread_date):
        if "yesterday" in thread_date.lower():
            return datetime.today() - timedelta(days=1)
        elif "hour" in thread_date.lower():
            return datetime.today()
        else:
            return super().parse_thread_date(thread_date)

    def parse_post_date(self, post_date):
        if "yesterday" in post_date.lower():
            return datetime.today() - timedelta(days=1)
        elif "hour" in post_date.lower():
            return datetime.today()
        else:
            return super().parse_post_date(post_date)

    def parse(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:
            # Standardize forum url
            if self.base_url not in forum_url:
                forum_url = response.urljoin(forum_url)

            yield Request(
                url=forum_url,
                headers=self.headers,
                meta=self.synchronize_meta(response),
                callback=self.parse_forum
            )

    def parse_forum(self, response):

        # Parse sub forums
        yield from self.parse(response)

        # Parse generic forum
        yield from super().parse_forum(response)

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class HoxForumScrapper(SiteMapScrapper):
    spider_class = HoxForumSpider


if __name__ == "__main__":
    pass
