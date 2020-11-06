import re
import os
import uuid

import dateparser
from datetime import datetime

from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 0.7
NO_OF_THREADS = 2


class ProxyBaseSpider(SitemapSpider):

    name = "proxybase_spider"

    # Url stuffs
    base_url = "http://proxy-base.com/"

    # Xpath stuffs
    forum_xpath = '//td[2]//a[contains(@href,"http://proxy-base.com/f") and not(contains(@href,"html"))]/@href'
    thread_xpath = '//tbody[contains(@id,"threadbits")]/tr'
    thread_first_page_xpath = './/tr[td[contains(@id, "td_threadtitle_")]]/@href'
    thread_last_page_xpath = './/td[4]//a[img]/@href'

    thread_date_xpath = './/span[@class="time"]/preceding-sibling::text()'

    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//div[@class="pagenav"]//span/strong/text()'

    post_date_xpath = '//table[contains(@id, "post")]//td[@class="thead"][1]'\
                      '/a[contains(@name,"post")]'\
                      '/following-sibling::text()[1]'

    avatar_xpath = '//div[@id="posts"]//tr[@valign="top"]/td[1]//a[contains(@rel, "nofollow") and img]'

    # Regex stuffs
    topic_pattern = re.compile(
        r".-(\d+).",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".dateline=(\d+).",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    post_datetime_format = '%d.%m.%Y'
    sitemap_datetime_format = '%d.%m.%Y'
    cloudfare_delay = 5
    handle_httpstatus_list = [503]

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """

        if thread_date is None:
            return datetime.today()

        return dateparser.parse(thread_date)

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """

        if post_date is None:
            return datetime.today()

        return dateparser.parse(post_date)

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                "cookiejar": uuid.uuid1().hex
            }
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                dont_filter=True,
                meta=self.synchronize_meta(response)
            )

    def parse_forum(self, response):
        # Check status 503
        if response.status == 503:
            request = response.request
            request.dont_filter = True
            request.meta = {
                "cookiejar": uuid.uuid1().hex
            }
            yield request
            return

        yield from super().parse_forum(response)

    def parse_thread(self, response):
        # Check status 503
        if response.status == 503:
            request = response.request
            request.dont_filter = True
            request.meta = {
                "cookiejar": uuid.uuid1().hex,
                "topic_id": response.meta.get("topic_id")
            }
            yield request
            return

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from self.parse_avatars(response)

    def parse_avatars(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Save avatar content
        for avatar in response.xpath(self.avatar_xpath):
            avatar_url = avatar.xpath('img/@src').extract_first()

            # Standardize avatar url
            if not avatar_url.lower().startswith("http"):
                avatar_url = self.base_url + avatar_url

            if 'image/svg' in avatar_url:
                continue

            # user_url = avatar.xpath('@href').extract_first()
            # print(user_url)
            match = self.avatar_name_pattern.findall(avatar_url)
            if not match:
                continue

            file_name = os.path.join(
                self.avatar_path,
                f'{match[0]}.jpg'
            )

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


class ProxyBaseScrapper(SiteMapScrapper):

    spider_class = ProxyBaseSpider
    site_name = 'proxybase.com'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500],
            }
        )
        return settings
