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


REQUEST_DELAY = 1
NO_OF_THREADS = 1

USERNAME = "vrx9"
MD5PASS = "db587913e1544e2169f44a5b7976c9a1"
PASSWORD = "Night#Vrx099"

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'


class VerifiedScSpider(SitemapSpider):

    name = 'verifiedsc_spider'

    # Url stuffs
    base_url = "https://verified.sc/"
    login_url = "https://verified.sc/login.php?do=login"

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
    sitemap_datetime_format = '%d.%m.%Y'
    post_datetime_format = '%d.%m.%Y, %H:%M'
    stop_text = 'you have exceeded the limit of page views in 24 hours'

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
            'Host': 'verified.sc',
            'Origin': 'https://verified.sc',
            'Referer': 'https://verified.sc/',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'User-Agent': USER_AGENT
        })

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
            callback=self.enter_code
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
                callback=self.parse,
                dont_filter=True,
                meta=self.synchronize_meta(response),
            )

        else:
            yield Request(
                self.base_url,
                headers=self.headers,
                callback=self.parse,
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

    def parse(self, response):
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
        if self.stop_text in response.text.lower():
            self.logger.info(
                'EXIT because of the text detected: '
                f'{self.stop_text}'
            )
            sys.exit()

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class VerifiedScScrapper(SiteMapScrapper):

    spider_class = VerifiedScSpider
    site_name = 'verified.sc'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
            }
        )
        return settings


if __name__ == "__main__":
    pass
