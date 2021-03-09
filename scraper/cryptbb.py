import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


USER = 'Cyrax011'
PASS = '4hr63yh38a61SDW0'

PROXY = 'http://127.0.0.1:8118'
DAILY_LIMIT = 100000

class CryptBBSpider(SitemapSpider):
    name = 'cryptbb_spider'
    base_url = 'http://cryptbb2gezhohku.onion/'

    # Xpaths
    login_form_xpath = '//form[@method="post"]'
    captcha_url_xpath = '//img[@id="captcha_img"]/@src'
    forum_xpath = '//a[contains(@href, "forumdisplay.php?fid=")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[@class="pagination_next"]/@href'
    thread_xpath = '//tr[@class="inline_row"]'
    thread_first_page_xpath = './/span[contains(@id,"tid_")]/a/@href'
    thread_last_page_xpath = './/td[contains(@class,"forumdisplay_")]/div'\
                             '/span/span[@class="smalltext"]/a[last()]/@href'
    thread_date_xpath = './/td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/text()[1]|'\
                        '//td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/span/@title'
    thread_pagination_xpath = '//div[@class="pagination"]'\
                              '//a[@class="pagination_previous"]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//span[@class="post_date"]/text()[1]|'\
                      '//span[@class="post_date"]/span/@title'\

    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'
    topic_pattern = re.compile(
        r".*tid=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Login Failed Message
    login_failed_xpath = '//li[contains(text(), "invalid username/password")]'

    # Other settings
    use_proxy = "Tor"
    retry_http_codes = [406, 429, 500, 503]
    sitemap_datetime_format = '%m-%d-%Y'
    post_datetime_format = '%m-%d-%Y'

    def start_requests(self):
        login_url = f"{self.base_url}member.php?action=login"
        yield Request(
            url=login_url,
            headers=self.headers,
            callback=self.proceed_for_login,
            dont_filter=True,
            meta={
                'proxy': PROXY
            },
            errback=self.check_site_error
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
        thread_date = thread_date.split(',')[0].strip()
        if not thread_date:
            return

        return datetime.strptime(
            thread_date,
            self.sitemap_datetime_format
        )

    def parse_post_date(self, post_date):
        # Standardize thread_date
        post_date = post_date.split(',')[0].strip()
        if not post_date:
            return
        return datetime.strptime(
            post_date,
            self.post_datetime_format
        )

    def proceed_for_login(self, response):
        if response.request.headers.get("Cookie"):
            captcha_url = response.xpath(
                self.captcha_url_xpath).extract_first()
            imagehash = response.xpath(
                '//input[@name="imagehash"]/@value').extract_first()
            self.logger.info(f'Downloading captcha from {captcha_url}')
            captcha = self.solve_captcha(
                captcha_url,
                response
            )
            self.logger.info(f'Captcha has been solved: {captcha}')

            formdata = {
                'username': USER,
                'password': PASS,
                'remember': 'yes',
                'imagestring': captcha,
                'imagehash': imagehash,
                'submit': 'Login',
                'action': 'do_login',
                'url': self.base_url,
            }
            yield FormRequest(
                url=f"{self.base_url}member.php?action=login",
                formdata=formdata,
                headers=self.headers,
                callback=self.parse_start,
                dont_filter=True,
                meta=self.synchronize_meta(response),
            )
        else:
            yield from self.start_requests()

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        # Check if login failed
        self.check_if_logged_in(response)
        
        if response.xpath("//li[contains(text(), 'The image verification code that you entered was incorrect')]").extract():
            yield from self.proceed_for_login(response)

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
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class CryptBBScrapper(SiteMapScrapper):

    spider_class = CryptBBSpider
    site_name = 'cryptbb_cryptbb2gezhohku'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "CLOSESPIDER_PAGECOUNT": DAILY_LIMIT
            }
        )
        return settings