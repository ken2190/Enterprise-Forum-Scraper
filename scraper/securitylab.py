import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper

class SecurityLabSpider(SitemapSpider):
    name = 'securitylab_spider'
    base_url = 'https://www.securitylab.ru'
    start_url = 'https://www.securitylab.ru/forum'

    # Xpaths
    forum_xpath = '//span[@class="forum-item-title"]/a/@href'
    thread_xpath = '//tr[td[@class="forum-column-title"]]'
    thread_first_page_xpath = './/span[@class="forum-item-title"]/a/@href'
    thread_last_page_xpath = './/span[@class="forum-item-pages"]'\
                             '/noindex[last()]/a/@href'
    thread_date_xpath = './/span[@class="forum-lastpost-date"]//a/text()[1]'
    pagination_xpath = '//a[@class="forum-page-next"]/@href'
    thread_pagination_xpath = '//a[@class="forum-page-previous"]/@href'
    thread_page_xpath = '//span[@class="forum-page-current"]/text()'
    post_date_xpath = '//div[@class="forum-post-date"]/span/text()'

    # Regex stuffs
    topic_pattern = re.compile(
        r"topic(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "On"
    post_datetime_format = '%d.%m.%Y %H:%M:%S'
    sitemap_datetime_format = '%d.%m.%Y %H:%M:%S'

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("forum/forum_count", len(all_forums))
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = response.urljoin(forum_url)

            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)


class SecurityLabScrapper(SiteMapScrapper):

    spider_class = SecurityLabSpider
    site_name = 'securitylab.ru'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings
