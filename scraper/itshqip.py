import re
from datetime import datetime

import dateparser as dateparser
from scrapy import Request
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


class ItshqipSpider(SitemapSpider):
    name = 'itshqip_spider'

    # Url stuffs
    base_url = "https://forum.itshqip.com/"
    change_language_url = "https://forum.itshqip.com/misc/language?language_id=1&redirect=https%3A%2F%2Fforum.itshqip.com%2F"

    # Xpath stuffs
    forum_xpath = '//h3[@class="nodeTitle"]/a[contains(@href, "forums/")]/@href'
    thread_xpath = '//ol[@class="discussionListItems"]/li'
    thread_first_page_xpath = './/h3[@class="title"]' \
                              '/a[contains(@href,"threads/")]/@href'
    thread_last_page_xpath = './/span[@class="itemPageNav"]' \
                             '/a[last()]/@href'
    thread_date_xpath = './/dl[@class="lastPostInfo"]' \
                        '//a[@class="dateTime"]/abbr/@data-time|' \
                        './/dl[@class="lastPostInfo"]' \
                        '//a[@class="dateTime"]/span/@title'
    pagination_xpath = '//nav/a[last()]/@href'
    thread_pagination_xpath = '//nav/a[@class="text"]/@href'
    thread_page_xpath = '//nav//a[contains(@class, "currentPage")]' \
                        '/text()'
    post_date_xpath = '//div[@class="privateControls"]' \
                      '//abbr[@class="DateTime"]/@data-time|'\
                      '//div[@class="privateControls"]' \
                      '//span[@class="DateTime"]/@title'

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
    use_proxy = "On"
    sitemap_datetime_format = '%b %d, %Y at %I:%M %p'
    post_datetime_format = '%b %d, %Y at %I:%M %p'

    def start_requests(self, cookiejar=None, ip=None):
        # Load meta
        meta = {}
        if cookiejar:
            meta["cookiejar"] = cookiejar
        if ip:
            meta["ip"] = ip

        # Branch choices requests
        if self.sitemap_url:
            yield Request(
                url=self.sitemap_url,
                headers=self.headers,
                callback=self.parse_sitemap,
                errback=self.check_site_error,
                dont_filter=True,
                meta=meta
            )
        else:
            yield Request(
                url=self.base_url,
                headers=self.headers,
                errback=self.check_site_error,
                dont_filter=True,
                callback=self.set_language_to_english,
                meta=meta
            )

    def set_language_to_english(self, response):
        yield Request(
            url=self.change_language_url,
            headers=self.headers,
            errback=self.check_site_error,
            dont_filter=True,
            meta=self.synchronize_meta(response)
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

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)

    def parse_thread_date(self, thread_date):
        try:  # check if datetime is a float
            date = datetime.fromtimestamp(float(thread_date))
        except:
            try:
                date = datetime.strptime(
                    thread_date.strip(),
                    self.post_datetime_format
                )
            except:
                date = dateparser.parse(thread_date)
        if date:
            return date.replace(tzinfo=None)

    def parse_post_date(self, post_date):
        try:  # check if datetime is a float
            date = datetime.fromtimestamp(float(post_date))
        except:
            try:
                date = datetime.strptime(
                    post_date.strip(),
                    self.post_datetime_format
                )
            except:
                date = dateparser.parse(post_date)
        if date:
            return date.replace(tzinfo=None)


class ItshqipScrapper(SiteMapScrapper):
    spider_class = ItshqipSpider
    site_name = 'itshqip.com'
    site_type = 'forum'

    def load_settings(self):
        spider_settings = super().load_settings()
        return spider_settings
