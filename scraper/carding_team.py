import time
import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from selenium import webdriver
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper

REQUEST_DELAY = 0.5
NO_OF_THREADS = 5
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'


class CardingTeamSpider(SitemapSpider):
    name = 'cardingteam_spider'
    base_url = "https://cardingteam.cc/"

    # Sitemap Stuffs
    sitemap_url = 'https://cardingteam.cc/sitemap-index.xml'
    forum_sitemap_xpath = '//url[loc[contains(text(),"sitemap-threads.xml")] and lastmod]'
    thread_sitemap_xpath = '//url[loc[contains(text(),"Thread-")] and lastmod]'
    thread_url_xpath = '//loc/text()'
    thread_lastmod_xpath = "//lastmod/text()"

    # Xpaths
    forum_xpath = '//a[contains(@href, "Forum-")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[@class="pagination_next"]/@href'
    thread_xpath = '//tr[@class="inline_row"]'
    thread_first_page_xpath = '//span[contains(@id,"tid_")]/a/@href'
    thread_last_page_xpath = '//td[contains(@class,"forumdisplay_")]/div'\
                             '/span/span[contains(@class,"smalltext")]'\
                             '/a[last()]/@href'
    thread_date_xpath = '//td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/text()[1]|'\
                        '//td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/span/@title'
    thread_pagination_xpath = '//div[@class="pagination"]'\
                              '//a[@class="pagination_previous"]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//span[@class="post_date2"]/text()[1]|'\
                      '//span[@class="post_date2"]/span/@title'\

    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )

    # custom settings
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None
        }
    }

    def get_cookies(self,):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument(f'user-agent={USER_AGENT}')
        browser = webdriver.Chrome(
            '/usr/local/bin/chromedriver',
            chrome_options=chrome_options)
        browser.get(self.base_url)
        time.sleep(1)
        cookies = browser.get_cookies()
        return '; '.join([
            f"{c['name']}={c['value']}" for c in cookies
        ])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cookies = self.get_cookies()
        self.headers.update({
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'user-agent': USER_AGENT,
            'cookie': cookies

        })

    def parse_thread_date(self, thread_date):
        return datetime.datetime.today()

    def parse_post_date(self, thread_date):
        return datetime.datetime.today()

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        print(self.headers)
        print(response.text)

        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            print(forum_url)
            continue
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


class CardingTeamScrapper(SiteMapScrapper):

    spider_class = CardingTeamSpider
    site_name = 'cardingteam.cc'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings
