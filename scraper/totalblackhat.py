import re
import uuid

from datetime import datetime
from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 0.3
NO_OF_THREADS = 10


class TotalBlackHatSpider(SitemapSpider):
    name = 'totalblackhat_spider'

    # Url stuffs
    base_url = "https://www.totalblackhat.net/"

    # Xpath stuffs
    forum_xpath = '//h3[@class="nodeTitle"]/a[contains(@href, "forums/")]/@href'
    thread_xpath = '//ol[@class="discussionListItems"]/li'
    thread_first_page_xpath = '//h3[@class="title"]'\
                              '/a[contains(@href,"threads/")]/@href'
    thread_last_page_xpath = '//span[@class="itemPageNav"]'\
                             '/a[last()]/@href'
    thread_date_xpath = '//dl[@class="lastPostInfo"]'\
                        '//a[@class="dateTime"]/abbr/@data-datestring|'\
                        '//dl[@class="lastPostInfo"]'\
                        '//a[@class="dateTime"]/span/text()'
    pagination_xpath = '//nav/a[last()]/@href'
    thread_pagination_xpath = '//nav/a[@class="text"]/@href'
    thread_page_xpath = '//nav//a[contains(@class, "currentPage")]'\
                        '/text()'
    post_date_xpath = '//div[@class="privateControls"]'\
                      '//span[@class="DateTime"]/text()|'\
                      '//div[@class="privateControls"]'\
                      '//abbr[@class="DateTime"]/@data-datestring'

    avatar_xpath = '//div[@class="avatarHolder"]/a/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"threads/.*\.(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    sitemap_datetime_format = '%b %d, %Y'
    post_datetime_format = '%b %d, %Y'
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS

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

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class TotalBlackHatScrapper(SiteMapScrapper):

    spider_class = TotalBlackHatSpider
    site_name = 'totalblackhat.net'
    site_type = 'forum'

    def load_settings(self):
        spider_settings = super().load_settings()
        return spider_settings
