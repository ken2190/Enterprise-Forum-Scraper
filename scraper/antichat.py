import sys
import os
import re
import json
import scrapy
from math import ceil
import configparser
from lxml.html import fromstring
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from datetime import datetime
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


USER = 'blacklotus2000@protonmail.com'
PASS = 'Night#Anti999'
REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class AntichatSpider(SitemapSpider):
    name = 'antichat_spider'
    sitemap_url = 'https://forum.antichat.ru/sitemap.php'
    # Xpath stuffs
    forum_xpath = "//loc/text()"
    thread_url_xpath = "//loc/text()"
    thread_xpath = "//url[lastmod]"
    thread_date_xpath = "//lastmod/text()"
    sitemap_datetime_format = '%Y-%m-%dT%H:%M:%S'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = 'https://forum.antichat.ru/'
        self.topic_pattern = re.compile(r'/threads/(\d+)/')
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.pagination_pattern = re.compile(r'page-(\d+)')
        self.headers = {
            'origin': 'https://forum.antichat.ru',
            'referer': 'https://forum.antichat.ru/',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': self.custom_settings.get("DEFAULT_REQUEST_HEADERS")
        }

    def parse_thread_date(self, thread_date):
        return datetime.strptime(
            thread_date.split('+')[0],
            self.sitemap_datetime_format
        )

    def proceed_for_login(self):
        login_url = 'https://forum.antichat.ru/login/login'
        params = {
            'login': USER,
            'password': PASS,
            'register': '0',
            "remember": '1',
            'cookie_check': '1',
            'redirect': 'https://forum.antichat.ru/',
            '_xfToken': ''
        }
        yield FormRequest(
            url=login_url,
            callback=self.parse,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
            )

    def parse(self, response):
        forums = response.xpath(
            '//div[@class="nodelistBlock nodeText"]'
            '/h3[@class="nodeTitle"]/a')
        subforums = response.xpath(
            '//ol[@class="subForumList"]'
            '//h4[@class="nodeTitle"]/a')
        forums.extend(subforums)
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = f'{self.base_url}{url}'

            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum,
            )

    def parse_forum(self, response):
        topic_blocks = response.xpath(
            '//ol[@class="discussionListItems"]/li[@id]')
        if not topic_blocks:
            topic_blocks = response.xpath(
                '//div[@class="uix_stickyThreads"]/li')
        for topic in topic_blocks:
            thread_url = topic.xpath(
                'div//h3[@class="title"]/a[@data-previewurl]/'
                '@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = f'{self.base_url}{thread_url}'
            match = self.topic_pattern.findall(thread_url)
            if not match:
                continue
            file_name = '{}/{}-1.html'.format(self.output_path, match[0])
            if os.path.exists(file_name):
                continue
            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={'topic_id': match[0]}
            )
        next_page = response.xpath(
            '//a[@class="text" and text()="Next >"]'
            )
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_forum,
            )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        paginated_value = pagination[0] if pagination else 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            # f.write(response.text.encode('cp1252'))
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'{topic_id}-{paginated_value} done..!')

        avatars = response.xpath(
            '//a[@data-avatarhtml="true"]/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if not avatar_url.startswith('http'):
                avatar_url = self.base_url + avatar_url
            match = self.avatar_name_pattern.findall(avatar_url)
            if not match:
                continue
            file_name = '{}/{}'.format(self.avatar_path, match[0])
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

        next_page = response.xpath(
            '//a[@class="text" and text()="Next >"]'
            )
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
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


class AntichatScrapper(SiteMapScrapper):

    spider_class = AntichatSpider

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
