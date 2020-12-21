import re
import os
import uuid

from datetime import datetime, timedelta
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


class CrackForumSpider(SitemapSpider):

    name = "crackforum"

    # Url stuffs
    base_url = "http://crack-forum.ru/"

    # Xpath stuffs

    # Forum xpath #
    forum_xpath = '//a[contains(@href, "forumdisplay.php?")]/@href'
    thread_xpath = '//tr[td[contains(@id, "td_threadtitle_")]]'
    thread_first_page_xpath = './/td[contains(@id, "td_threadtitle_")]/div'\
                              '/a[contains(@href, "showthread.php?")]/@href'
    thread_last_page_xpath = './/td[contains(@id, "td_threadtitle_")]/div/span'\
                             '/a[contains(@href, "showthread.php?")]'\
                             '[last()]/@href'
    thread_date_xpath = './/span[@class="time"]/preceding-sibling::text()'

    pagination_xpath = '//div[@class="pagenav"]'\
                       '//a[@class="smallfont" and text()=">"]/@href'
    thread_pagination_xpath = '//div[@class="pagenav"]'\
                              '//a[@class="smallfont" and text()="<"]/@href'
    thread_page_xpath = '//div[@class="pagenav"]//span/strong/text()'
    post_date_xpath = '//table[contains(@id, "post")]//td[@class="thead"][1]'\
                      '/a[contains(@name,"post")]'\
                      '/following-sibling::text()[1]'
    avatar_xpath = '//a[contains(@href, "member.php?")]/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    post_datetime_format = '%d.%m.%Y, %H:%M'
    sitemap_datetime_format = '%d.%m.%Y'

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.strip()
        if not thread_date:
            return
        return dateparser.parse(thread_date)

    def parse_post_date(self, post_date):
        post_date = post_date.strip()
        if not post_date:
            return
        return dateparser.parse(post_date)

    def start_requests(self, ):
        url = f'{self.base_url}forum.php'
        yield Request(
            url=url,
            headers=self.headers,
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:

            # Standardize url
            if not forum_url.startswith('http'):
                forum_url = self.base_url + forum_url
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class CrackForumScrapper(SiteMapScrapper):

    spider_class = CrackForumSpider
    site_name = 'crack-forum.ru'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 502],
            }
        )
        return settings
