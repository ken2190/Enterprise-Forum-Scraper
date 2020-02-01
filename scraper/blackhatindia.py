import time
import requests
import os
import json
import re
import scrapy
from math import ceil
from copy import deepcopy
from urllib.parse import urlencode
import configparser
from scrapy.http import Request, FormRequest
from lxml.html import fromstring
from scrapy.crawler import CrawlerProcess
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


USER = 'Cyrax_011'
PASS = 'Night#India065'

REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class BlackHatIndiaSpider(SitemapSpider):
    name = 'blackhatindia_spider'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://fraudstercrew.su"
        self.topic_pattern = re.compile(r'threads/.*\.(\d+)/')
        self.avatar_name_pattern = re.compile(r'members/(.*?)/')
        self.pagination_pattern = re.compile(r'.*page-(\d+)')
        self.start_url = self.base_url
        self.headers = {
            'user-agent': self.custom_settings.get("DEFAULT_REQUEST_HEADERS"),
            'referer': 'https://forum.blackhatindia.ru/',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1'
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.parse
        )

    def get_token(self, response):
        match = re.findall(r'csrf: \'(.*?)\'', response.text)
        params = {
            '_xfRequestUri': '/',
            '_xfWithData': '1',
            '_xfToken': match[0],
            '_xfResponseType': 'json'
        }
        print('params')
        print(params)
        token_url = 'https://forum.blackhatindia.ru/login/?' + urlencode(params)
        yield Request(
            url=token_url,
            headers=response.request.headers,
            callback=self.proceed_for_login
        )

    def proceed_for_login(self, response):
        json_response = json.loads(response.text)
        html_response = fromstring(json_response['html']['content'])
        token = html_response.xpath(
            '//input[@name="_xfToken"]/@value')[0]
        params = {
            'login': USER,
            'password': PASS,
            "remember": '1',
            '_xfToken': token
        }
        login_url = 'https://forum.blackhatindia.ru/login/login'
        yield scrapy.FormRequest(
            login_url,
            callback=self.parse,
            formdata=params,
            headers=response.request.headers,
            dont_filter=True,
        )

    def parse(self, response):
        forums = response.xpath(
            '//h3[@class="node-title"]/a')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            yield Request(
                url=url,
                headers=response.request.headers,
                callback=self.parse_forum
            )
        sub_forums = response.xpath(
            '//ol[@class="node-subNodeFlatList"]/li/a')
        for sub_forum in sub_forums:
            url = sub_forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            yield Request(
                url=url,
                headers=response.request.headers,
                callback=self.parse_forum
            )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//a[@data-preview-url]')
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
                headers=response.request.headers,
                callback=self.parse_thread,
                meta={'topic_id': topic_id[0]}
            )

        next_page = response.xpath(
            '//a[@class="pageNav-jump pageNav-jump--next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=response.request.headers,
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
            print(f'{topic_id}-{paginated_value} done..!')

        avatars = response.xpath(
            '//div[@class="message-avatar-wrapper"]/a')
        for avatar in avatars:
            avatar_url = avatar.xpath('img/@src').extract_first()
            if not avatar_url:
                continue
            if not avatar_url.startswith('http'):
                avatar_url = self.base_url + avatar_url
            user_id = avatar.xpath('@href').extract_first()
            match = self.avatar_name_pattern.findall(user_id)
            if not match:
                continue
            file_name = '{}/{}'.format(self.avatar_path, match[0])
            if os.path.exists(file_name):
                continue
            yield Request(
                url=avatar_url,
                headers=response.request.headers,
                callback=self.parse_avatar,
                meta={
                    'file_name': file_name,
                    'user_id': user_id
                }
            )

        next_page = response.xpath(
            '//a[@class="pageNav-jump pageNav-jump--next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=response.request.headers,
                callback=self.parse_thread,
                meta={'topic_id': topic_id}
            )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        with open(file_name, 'wb') as f:
            f.write(response.body)
            print(f"Avatar for user {response.meta['user_id']} done..!")


class BlackHatIndiaScrapper(SiteMapScrapper):

    spider_class = BlackHatIndiaSpider

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
                'RETRY_HTTP_CODES': [403, 429, 500, 503, 504],
            }
        )
        return settings
