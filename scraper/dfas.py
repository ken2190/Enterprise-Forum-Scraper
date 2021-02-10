import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


USER = 'Cyrax_011'
PASS = 'c2Yv9EP8MsgGHJr'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'

PROXY = 'http://127.0.0.1:8118'


class DfasSpider(SitemapSpider):
    name = 'dfas_spider'
    base_url = 'http://annxjgfo6xo4igamx5sbeiocimkdqrjux5ga27smny6vdx4dgzn2wcqd.onion/'
    login_url = 'http://annxjgfo6xo4igamx5sbeiocimkdqrjux5ga27smny6vdx4dgzn2wcqd.onion/login.php?action=in'

    # Xpaths
    forum_xpath = '//a[contains(@href, "viewforum.php")]/@href'
    pagination_xpath = '//a[@rel="next"]/@href'
    thread_xpath = '//div[@class="inbox"]//tr[contains'\
                   '(@class, "roweven") or contains(@class, "rowodd")]'
    thread_first_page_xpath = './/tr[contains(@class, "roweven") or '\
                              'contains(@class, "rowodd")]'\
                              '//a[contains(@href,"viewtopic.php")]/@href'
    thread_date_xpath = './/td[@class="tcr"]/a/text()'
    thread_pagination_xpath = '//a[@rel="next"]/@href'
    thread_page_xpath = '//p[@class="pagelink conl"]/strong/text()'
    post_date_xpath = '//div[contains(@class, "blockpost")]/h2/span/a/text()'

    # Login Failed Message
    login_failed_xpath = '//ul[contains(@class, "error-list")]'

    # Regex stuffs
    topic_pattern = re.compile(
        r"id=(\d+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*p=(\d+)",
        re.IGNORECASE
    )
    # Other settings
    use_proxy = "Tor"
    sitemap_datetime_format = '%Y-%m-%d %H:%M:%S'
    post_datetime_format = '%Y-%m-%d %H:%M:%S'

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

    def start_requests(self):
        yield FormRequest(
            url=self.login_url,
            callback=self.proceed_for_login,
            headers=self.headers,
            meta={
                'proxy': PROXY
            }
        )

    def proceed_for_login(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        csrf_token = response.xpath(
            '//input[@name="csrf_token"]/@value').extract_first()
        formdata = {
            'csrf_token': csrf_token,
            'redirect_url': 'http://annxjgfo6xo4igamx5sbeiocimkdqrjux5ga27smny6vdx4dgzn2wcqd.onion/index.php',
            "form_sent": "1",
            "login": "Login",
            'req_password': PASS,
            'req_username': USER,
        }

        yield FormRequest(
            url=self.login_url,
            callback=self.parse_start,
            headers=self.headers,
            formdata=formdata,
            dont_filter=True,
            meta=self.synchronize_meta(response),
        )

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        thread_date = thread_date.strip()

        if "aujourd'hui" in thread_date.lower():
            return datetime.today()
        elif "hier" in thread_date.lower():
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

        if "aujourd'hui" in post_date.lower():
            return datetime.today()
        elif "hier" in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        # Check if login failed
        self.check_if_logged_in(response)
        
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
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)


class DfasScrapper(SiteMapScrapper):

    spider_class = DfasSpider
    site_name = 'dfas (annxjgfo6xo4igamx5sbeiocimkdqrjux5ga27smny6vdx4dgzn2wcqd..onion)'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update({
            'RETRY_HTTP_CODES': [406, 429, 500, 503]
        })
        return settings
