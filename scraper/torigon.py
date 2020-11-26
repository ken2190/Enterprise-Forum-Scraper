import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


REQUEST_DELAY = 0.8
NO_OF_THREADS = 2

USER = 'Cyrax_011'
PASS = 'WLZukoZl'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'

PROXY = 'http://127.0.0.1:8118'


class TorigonSpider(SitemapSpider):
    name = 'torigon_spider'
    base_url = 'http://torigonsn3d63cldhr76mkfdzo3tndnl2tftiek55i2vilscufer6ryd.onion/'

    # Xpaths
    forum_xpath = '//a[contains(@class, "forumtitle")]/@href'
    thread_xpath = '//ul[@class="topiclist topics"]/li'
    thread_first_page_xpath = './/a[contains(@class, "topictitle")]/@href'
    thread_last_page_xpath = './/div[@class="pagination"]'\
                             '/ul/li[last()]/a/@href'
    thread_date_xpath = './/dd[@class="lastpost"]/span/text()[last()]'
    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//div[@class="pagination"]//'\
                        'li[@class="active"]/span/text()'
    post_date_xpath = '//p[@class="author"]/descendant::text()'

    # Regex stuffs
    topic_pattern = re.compile(
        r"t=(\d+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*start=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = '%a %b %d, %Y'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update({
            "user-agent": USER_AGENT
        })

    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip"]
            if response.meta.get(key)
        }

        meta.update(default_meta)
        meta.update({'proxy': PROXY})

        return meta

    def parse_post_date(self, post_date):
        return datetime.today()

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.proceed_for_login,
            meta={
                'proxy': PROXY
            }
        )

    def proceed_for_login(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        login_url = 'http://torigonsn3d63cldhr76mkfdzo3tndnl2tftiek55i2vilscufer6ryd.onion/ucp.php?mode=login'
        creation_time = response.xpath(
            '//input[@name="creation_time"]/@value').extract_first()
        form_token = response.xpath(
            '//input[@name="form_token"]/@value').extract_first()
        sid = response.xpath(
            '//input[@name="sid"]/@value').extract_first()
        params = {
            'username': USER,
            'password': PASS,
            'autologin': 'on',
            'redirect': './index.php?',
            'creation_time': creation_time,
            'form_token': form_token,
            'sid': sid,
            'login': 'Login'
        }
        yield FormRequest(
            url=login_url,
            callback=self.parse,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
            meta=self.synchronize_meta(response),
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
                forum_url = self.base_url + forum_url
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_forum(self, response):
        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        sub_forums = response.xpath(
            '//ul[@class="topiclist forums"]'
            '//a[@class="forumtitle"]/@href').extract()
        for forum_url in sub_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )
        else:
            yield from super().parse_forum(response)

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)


class TorigonScrapper(SiteMapScrapper):

    spider_class = TorigonSpider
    site_name = 'torigon'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings
