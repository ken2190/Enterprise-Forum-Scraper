import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


REQUEST_DELAY = 1
NO_OF_THREADS = 1

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'

PROXY = 'http://127.0.0.1:8118'


class CebulkaSpider(SitemapSpider):
    name = 'cebulka_spider'
    base_url = 'http://cebulka7uxchnbpvmqapg5pfos4ngaxglsktzvha7a5rigndghvadeyd.onion/'

    # Xpaths
    forum_xpath = '//a[contains(@href, "viewforum.php")]/@href'
    pagination_xpath = '//p[@class="paging"]/a[last()]/@href'
    thread_xpath = '//div[@class="main-content main-forum forum-noview"]'\
                   '/div[contains(@id, "topic")]'
    thread_first_page_xpath = './/h3[@class="hn"]/a/@href'
    thread_last_page_xpath = './/span[@class="item-nav"]/a[last()]/@href'
    thread_date_xpath = './/li[@class="info-lastpost"]/strong/a/text()'
    thread_pagination_xpath = '//a[text()="Poprzednia"]/@href'
    thread_page_xpath = '//p[@class="paging"]/strong/text()'
    post_date_xpath = '//span[@class="post-link"]/a/text()'

    avatar_xpath = '//li[@class="useravatar"]/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"id=(\d+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*p=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    sitemap_datetime_format = '%Y-%m-%d %p'
    post_datetime_format = '%Y-%m-%d %p'
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update({
            "user-agent": USER_AGENT
        })

    def start_requests(self):
        start_url = 'http://cebulka7uxchnbpvmqapg5pfos4ngaxglsktzvha7a5rigndghvadeyd.onion/index.php'
        formdata = {
            'confirm_cancel': '',
            'prev_url': '',
            'no_captcha': '',
        }
        yield FormRequest(
            url=start_url,
            headers=self.headers,
            formdata=formdata,
            meta={
                'proxy': PROXY
            }
        )

    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip"]
            if response.meta.get(key)
        }

        meta.update(default_meta)
        meta.update({'proxy': PROXY})

        return meta

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        thread_date = thread_date.strip()

        if 'dzisiaj' in thread_date.lower():
            return datetime.today()
        elif "wczoraj" in thread_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        post_date = post_date.strip()

        if "dzisiaj" in post_date.lower():
            return datetime.today()
        elif "wczoraj" in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            # if not forum_url.endswith('id=1'):
            #     continue
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class CebulkaScrapper(SiteMapScrapper):

    spider_class = CebulkaSpider
    site_name = 'cebulka (cebulka7uxchnbpvmqapg5pfos4ngaxglsktzvha7a5rigndghvadeyd.onion)'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update({
            'RETRY_HTTP_CODES': [406, 429, 500, 503]
        })
        return settings
