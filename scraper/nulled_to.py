import os
import re
import traceback

from datetime import (
    datetime,
    timedelta
)

import dateparser
from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

REQUEST_DELAY = .6
NO_OF_THREADS = 7


class NulledSpider(SitemapSpider):
    name = 'nulled_spider'

    # Url stuffs
    base_url = "https://www.nulled.to"
    start_url = 'https://www.nulled.to'

    # Xpath stuffs
    forum_xpath = "//h4//a/@href"
    thread_xpath = "//tr[contains(@id,'trow')]"
    thread_date_xpath = ".//td[@class='col_f_post']/ul/li[contains(@class,'blend_links')]/a/text()"
    thread_first_page_xpath = ".//a[@itemprop='url' and contains(@id, 'tid-link-')]/@href"
    thread_last_page_xpath = ".//ul[contains(@class,'mini_pagination')]/li[last()]/a/@href"
    pagination_xpath = "//li[@class='next']/a/@href"
    thread_pagination_xpath = "//li[@class='prev']/a/@href"
    thread_page_xpath = "//li[@class='page active']/text()"
    post_date_xpath = "//div[@class='post_body']/div[@class='post_date']/abbr[@class='published']/@title"
    avatar_xpath = "//li[@class='avatar']/img/@src"

    # Regex stuffs
    topic_pattern = re.compile(
        r"topic/(\d+).*",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/profile/photo-(\d+\.\w+)\?.*",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page-(\d+)",
        re.IGNORECASE
    )

    # Other settings
    sitemap_datetime_format = "%d %b, %Y"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    use_proxy = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "Referer": "https://www.nulled.to/",
                "Sec-fetch-mode": "navigate",
                "Sec-fetch-site": "none",
                "Sec-fetch-user": "?1",
            }
        )

    def start_requests(self):
        # Proceed for banlist
        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse_start,
        )

    def parse_start(self, response):

        # Synchronize user agent in cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("forum/forum_count", len(all_forums))
        for forum in all_forums:

            if self.base_url not in forum:
                forum = self.base_url + '/' + forum

            yield Request(
                url=forum,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):

        # Save avatar content
        yield from self.parse_avatars(response)

        # Parse generic thread response
        yield from super().parse_thread(response)


    def parse_avatars(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Save avatar content
        all_avatars = response.xpath(self.avatar_xpath).extract()
        for avatar_url in all_avatars:

            temp_url = avatar_url
            # Standardize avatar url
            if not avatar_url.lower().startswith("http"):
                temp_url = response.urljoin(avatar_url)

            avatar_url = temp_url

            if 'image/svg' in avatar_url:
                continue

            file_name = self.get_avatar_file(avatar_url)

            if file_name is None:
                continue

            if os.path.exists(file_name):
                continue

            yield Request(
                url=avatar_url,
                headers=self.headers,
                callback=self.parse_avatar,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "file_name": file_name
                    }
                ),
            )


class NulledToScrapper(SiteMapScrapper):

    spider_class = NulledSpider
    site_name = 'nulled.to'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "DOWNLOAD_DELAY": REQUEST_DELAY,
                "CONCURRENT_REQUESTS": NO_OF_THREADS,
                "CONCURRENT_REQUESTS_PER_DOMAIN": NO_OF_THREADS,
                'RETRY_HTTP_CODES': [403, 429, 500, 503, 504],
            }
        )
        return settings
