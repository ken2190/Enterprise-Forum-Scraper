import os
import re
import sys
import scrapy
from math import ceil
import configparser
from scrapy import (
    Request,
    FormRequest
)

from datetime import datetime, timedelta

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 4
NO_OF_THREADS = 1

USERNAME = "blackrhino"
MD5PASS = "7a3a4f8cbe6d26725a900af4be9256aa"
PASSWORD = "Night#Rhino02"

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/71.0'

PROXY = 'http://127.0.0.1:8118'


class VerifiedScSpider(SitemapSpider):

    name = 'verifiedsc_spider'

    # Url stuffs
    base_url = "http://verified2ebdpvms.onion/"
    login_url = "http://verified2ebdpvms.onion/login.php?do=login"

    # Xpath stuffs
    forum_xpath = '//a[contains(@href, "forumdisplay.php?")]/@href'
    thread_xpath = '//tr[td[contains(@id, "td_threadtitle_")]]'
    thread_first_page_xpath = '//td[contains(@id, "td_threadtitle_")]/div'\
                              '/a[contains(@href, "showthread.php?")]/@href'
    thread_last_page_xpath = '//td[contains(@id, "td_threadtitle_")]/div/span'\
                             '/a[contains(@href, "showthread.php?")]'\
                             '[last()]/@href'
    thread_date_xpath = '//span[@class="time"]/preceding-sibling::text()'

    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//div[@class="pagenav"]//span/strong/text()'
    post_date_xpath = '//table[contains(@id, "post")]//td[@class="thead"]'\
                      '/a[contains(@name,"post")]/following-sibling::text()'
    avatar_xpath = '//a[contains(@href, "member.php?")]/img/@src'

    # Other settings
    use_proxy = False
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = '%d.%m.%Y'
    post_datetime_format = '%d.%m.%Y, %H:%M'
    stop_text = [
        'you have exceeded the limit of page views in 24 hours',
        'you have reached the limit of viewing topics per day.'
    ]

    # Regex stuffs
    topic_pattern = re.compile(
        r".*t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r"&page=(\d+)",
        re.IGNORECASE
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update({
            'Host': 'verified2ebdpvms.onion',
            'Referer': self.base_url,
            'User-Agent': USER_AGENT
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
        formdata = {
            "vb_login_username": USERNAME,
            "vb_login_password": "",
            "vb_login_md5password": MD5PASS,
            "vb_login_md5password_utf": MD5PASS,
            "cookieuser": '1',
            "securitytoken": "guest",
            "s": "",
            "url": "/",
            "do": "login"
        }

        yield FormRequest(
            self.login_url,
            formdata=formdata,
            headers=self.headers,
            callback=self.enter_code,
            meta={
                'proxy': PROXY
            }
        )

    def enter_code(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        code_number = response.xpath(
            '//div[@class="personalCodeBrown"]/font/text()').extract_first()
        print(self.backup_codes)
        print(code_number)
        code_value = self.backup_codes[int(code_number)-1]\
            if code_number else None
        if code_value:
            formdata = {
                'code': code_value
            }
            values = response.xpath('//form[@id="codeEnterForm"]/input')
            for v in values:
                key = v.xpath('@name').extract_first()
                value = v.xpath('@value').extract_first()
                formdata.update({key: value})
            yield FormRequest(
                self.login_url,
                formdata=formdata,
                headers=self.headers,
                callback=self.after_login,
                dont_filter=True,
                meta=self.synchronize_meta(response),
            )

        else:
            yield Request(
                self.base_url,
                headers=self.headers,
                callback=self.after_login,
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

        if 'today' in thread_date.lower():
            return datetime.today()
        elif "yesterday" in thread_date.lower():
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

        if "today" in post_date.lower():
            return datetime.today()
        elif "yesterday" in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def after_login(self, response):
        # Synchronize user agent in cloudfare middleware
        self.synchronize_headers(response)
        main_forum_url = 'http://verified2ebdpvms.onion/forum.php'
        yield Request(
            url=main_forum_url,
            headers=self.headers,
            callback=self.parse_start,
            meta=self.synchronize_meta(response),
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            # if 'f=90' not in forum_url:
            #     continue
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):
        if any(text in response.text.lower() for text in self.stop_text):
            self.logger.info(
                'EXIT because of the text detected: '
                f'{self.stop_text}'
            )
            os._exit(0)
        else:
            # Parse generic thread
            yield from super().parse_thread(response)

            # Parse generic avatar
            yield from super().parse_avatars(response)


class VerifiedScScrapper(SiteMapScrapper):

    spider_class = VerifiedScSpider
    site_name = 'verified (verified2ebdpvms.onion)'
