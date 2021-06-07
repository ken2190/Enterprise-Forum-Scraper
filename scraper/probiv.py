import re
from datetime import datetime

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


class ProbivSpider(SitemapSpider):
    name = "probiv_spider"

    # Url stuffs
    base_url = "https://probiv.one"

    # Xpath stuffs
    forum_xpath = "//h3[@class='node-title']/a/@href"
    pagination_xpath = "//a[contains(@class,'pageNav-jump--next')]/@href"

    thread_xpath = "//div[contains(@class,'js-threadListItem')]"
    thread_first_page_xpath = ".//div[@class='structItem-title']/a[starts-with(@href,'/threads/')]/@href"
    thread_last_page_xpath = ".//div[@class='structItem-minor']/span/a[last()]/@href"
    thread_date_xpath = ".//div[contains(@class,'structItem-cell--latest')]/a/time/@data-time"

    thread_pagination_xpath = "//a[contains(@class,'pageNav-jump--next')]/@href"
    thread_page_xpath = "//li[contains(@class,'pageNav-page--current')]/a/text()"
    post_date_xpath = "//article//a/time/@data-time"
    avatar_xpath = "//div[@class='message-avatar-wrapper']/a/img/@src"

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    topic_pattern = re.compile(
        r".[.](\d+)/*",
        re.IGNORECASE
    )

    # Other settings
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"
    use_proxy = "On"

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)

    def parse_thread_date(self, thread_date):
        try:
            return datetime.fromtimestamp(float(thread_date))
        except Exception:
            return datetime.strptime(
                thread_date.strip(),
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        try:
            return datetime.fromtimestamp(float(post_date))
        except Exception:
            return datetime.strptime(
                post_date.strip(),
                self.post_datetime_format
            )


class ProbivScrapper(SiteMapScrapper):
    spider_class = ProbivSpider
    site_type = 'forum'


if __name__ == "__main__":
    pass
