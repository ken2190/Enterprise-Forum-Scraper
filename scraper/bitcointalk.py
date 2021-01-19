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

class BitcoinTalkSpider(SitemapSpider):

    name = "bitcointalk_spider"

    # Url stuffs
    base_url = "https://bitcointalk.org/"

    # Xpath stuffs
    forum_xpath = "//td[@class=\"windowbg2\"]/b/a/@href|" \
                  "//td[@class=\"windowbg3\"]/span/a/@href"
    pagination_xpath = "//span[@class=\"prevnext\"][last()]/a/@href"

    thread_xpath = "//tr[td[contains(@class,\"windowbg\")][5]]"
    thread_first_page_xpath = ".//span[contains(@id,\"msg\")]/a/@href"
    thread_last_page_xpath = ".//small[@id]/a[not(contains(text(),\"All\"))][last()]/@href"
    thread_date_xpath = ".//td[contains(@class,\"lastpostcol\")]/span/text()[contains(.,\",\")]|" \
                        ".//td[contains(@class,\"lastpostcol\")]/span/b/text()"

    post_date_xpath = "//div[contains(@id,\"subject\")]/" \
                      "following-sibling::div[@class=\"smalltext\"]/" \
                      "text()[contains(.,\",\")]|" \
                      "//div[contains(@id,\"subject\")]/" \
                      "following-sibling::div[@class=\"smalltext\"]/b/text()"
    thread_page_xpath = "//td[@class=\"middletext\"]/text()[contains(.,\"[\")]/following-sibling::b[1]/text()"
    thread_pagination_xpath = "//td[@class=\"middletext\"]/span[a[text()=\"«\"]]/a/@href"
    avatar_xpath = "//div[@class=\"smalltext\"]/div/img/@src"

    # Regex stuffs
    topic_pattern = re.compile(
        r"topic=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    sitemap_datetime_format = "%B %d, %Y, %I:%M:%S %p"
    post_datetime_format = "%B %d, %Y, %I:%M:%S %p"

    def parse_thread_date(self, thread_date):

        # Check thread date validation
        if not thread_date:
            return

        # Standardize
        thread_date = thread_date.strip()

        # Parsing stuffs
        if "today" in thread_date.lower():
            return datetime.today()
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):

        # Check thread date validation
        if not post_date:
            return

        # Standardize
        post_date = post_date.strip()

        # Parsing stuffs
        if "today" in post_date.lower():
            return datetime.today()
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def parse(self, response):

        # Synchronize user agent for cloudfare middlewares
        self.synchronize_headers(response)

        # # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("forum/forum_count", len(all_forums))
        
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


class BitCoinTalkScrapper(SiteMapScrapper):

    spider_class = BitcoinTalkSpider
    site_type = 'forum'


if __name__ == "__main__":
    pass
