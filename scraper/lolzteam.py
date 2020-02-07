import time
import requests
import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from datetime import datetime
from selenium import webdriver
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


USER = "darkcylon1@protonmail.com"
PASS = "Night#Kgg2"
REQUEST_DELAY = 0.4
NO_OF_THREADS = 8
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'


class LolzSpider(SitemapSpider):
    name = 'lolz_spider'
    sitemap_url = 'https://www.lolzteam.online/sitemap.xml'
    # Xpath stuffs
    forum_sitemap_xpath = "//loc/text()"
    thread_url_xpath = "//loc/text()"
    thread_sitemap_xpath = '//url[loc[contains(text(), "/threads/")] and lastmod]'
    thread_lastmod_xpath = "//lastmod/text()"
    sitemap_datetime_format = '%Y-%m-%dT%H:%M:%S'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None
        }
    }

    def get_cookies(self,):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
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
        self.base_url = "https://lolzteam.online/"
        self.topic_pattern = re.compile(r'threads/(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page-(\d+)')
        cookies = self.get_cookies()
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9,hi;q=0.8,ru;q=0.7',
            'cache-control': 'max-age=0',
            'referer': 'https://lolzteam.online/',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'cookie': cookies,
            "user-agent": USER_AGENT,
        }

    def proceed_for_login(self):
        data = {
            "login": USER,
            "password": PASS,
            "remember": "1",
            "stopfuckingbrute1337": "1",
            "cookie_check": "1",
            "_xfToken": "",
            "redirect": "https://lolzteam.online/"
        }
        login_url = 'https://lolzteam.online/login/login'
        yield FormRequest(
            url=login_url,
            formdata=data,
            headers=self.headers,
        )

    def parse_thread_date(self, thread_date):
        return datetime.strptime(
            thread_date.split('+')[0],
            self.sitemap_datetime_format
        )

    def parse(self, response):
        forums = response.xpath(
            '//ol[@class="nodeList"]//h3[@class="nodeTitle"]'
            '/a[contains(@href, "forums/")]')
        subforums = response.xpath(
            '//ol[@class="nodeList"]//h4[@class="nodeTitle"]'
            '/a[contains(@href, "forums/")]')
        forums.extend(subforums)
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_forum(self, response):
        self.logger.info('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//div[@class="discussionListItem--Wrapper"]'
            '/a[contains(@href, "")]')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = self.topic_pattern.findall(thread_url)
            if not topic_id:
                continue
            file_name = '{}/{}-1.html'.format(self.output_path, topic_id[0])
            if os.path.exists(file_name):
                continue
            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={'topic_id': topic_id[0]}
            )

        next_page_url = response.xpath(
            '//nav/a[contains(@class,"currentPage")]'
            '/following-sibling::a[1]/@href').extract_first()
        if next_page_url:
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        paginated_value = pagination[0] if pagination else 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'{topic_id}-{paginated_value} done..!')

        avatars = response.xpath(
            '//div[@class="avatarHolder"]/a/span[@style and @class]')
        for avatar in avatars:
            avatar_url = avatar.xpath('@style').re(r'url\(\'(.*?)\'\)')
            if not avatar_url:
                continue
            if self.base_url not in avatar_url[0]:
                avatar_url = self.base_url + avatar_url[0]
            name_match = self.avatar_name_pattern.findall(avatar_url)
            if not name_match:
                continue
            name = name_match[0]
            file_name = '{}/{}'.format(self.avatar_path, name)
            if os.path.exists(file_name):
                continue
            yield Request(
                url=avatar_url,
                headers=self.headers,
                callback=self.parse_avatar,
                meta={
                    'file_name': file_name,
                }
            )

        next_page_url = response.xpath(
            '//nav/a[contains(@class,"currentPage")]'
            '/following-sibling::a[1]/@href').extract_first()
        if next_page_url:
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={'topic_id': topic_id}
            )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        file_name_only = file_name.rsplit('/', 1)[-1]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            self.logger.info(f"Avatar {file_name_only} done..!")


class LolzScrapper(SiteMapScrapper):

    spider_class = LolzSpider

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
