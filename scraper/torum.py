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
from copy import deepcopy
from datetime import datetime, timedelta

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


USERNAME = "vrx9"
MD5PASS = "db587913e1544e2169f44a5b7976c9a1"
PASSWORD = "Night#Vrx099"

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'

PROXY = 'http://127.0.0.1:8118'


class TorumSpider(SitemapSpider):

    name = 'torum_spider'

    # Url stuffs
    base_url = "http://torum43tajnrxritn4iumy75giwb5yfw6cjq2czjikhtcac67tfif2yd.onion/"
    login_url = f'{base_url}ucp.php?mode=login'
    captcha_base_url = f'{base_url}captcha/'

    # Xpath stuffs
    captcha_form_xpath = '//form[@method="post"]'
    login_form_xpath = '//form[@id="login"]'
    captcha_url_xpath = '//img[@src="image.php"]/@src'
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
    post_date_xpath = '//p[@class="author"]/text()[last()]'

    # Other settings
    use_proxy = True
    sitemap_datetime_format = '%d %b %Y'
    post_datetime_format = '%d %b %Y'

    # Regex stuffs
    topic_pattern = re.compile(
        r".*&t=(\d+)",
        re.IGNORECASE
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update({
            'Host': 'torum43tajnrxritn4iumy75giwb5yfw6cjq2czjikhtcac67tfif2yd.onion',
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

        yield Request(
            self.base_url,
            headers=self.headers,
            callback=self.enter_captcha,
            dont_filter=True,
            meta={
                'proxy': PROXY
            }
        )

    def enter_captcha(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        if response.xpath('//input[@value="Verify"]'):
            if response.request.headers.get("Cookie"):
                # Load captcha url
                captcha_img = response.xpath(
                    self.captcha_url_xpath).extract_first()
                captcha_img_url = f'{self.captcha_base_url}{captcha_img}'
                print(f'Downloading captcha from {captcha_img_url}')
                captcha = self.solve_captcha(
                    captcha_img_url,
                    response
                )
                self.logger.info(f'Captcha has been solved: {captcha}')
                formdata = {
                    'input': captcha,
                }
                yield FormRequest.from_response(
                    response=response,
                    formxpath=self.captcha_form_xpath,
                    formdata=formdata,
                    headers=self.headers,
                    callback=self.proceed_for_login,
                    dont_filter=True,
                    meta=self.synchronize_meta(response),
                )
            else:
                yield from self.start_requests()
        else:
            yield from self.proceed_for_login(response)

    def proceed_for_login(self, response):
        formdata = {
            'username': USERNAME,
            'password': PASSWORD
        }
        yield FormRequest.from_response(
            response=response,
            formxpath=self.login_form_xpath,
            formdata=formdata,
            headers=self.headers,
            callback=self.parse_start,
            dont_filter=True,
            meta=self.synchronize_meta(response),
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("forum/forum_count", len(all_forums))
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            # if 'f=26' not in forum_url:
            #     continue
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):
        # Parse generic thread
        yield from super().parse_thread(response)


class TorumScrapper(SiteMapScrapper):

    spider_class = TorumSpider
    site_name = 'torum'
    site_type = 'forum'
