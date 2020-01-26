import time
import requests
import os
import json
import re
import scrapy
from math import ceil
import configparser
from urllib.parse import urlencode
from lxml.html import fromstring
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from scraper.base_scrapper import SiteMapScrapper


USER = 'Cyrax_011'
PASS = 'Night#India065'

REQUEST_DELAY = 0.3
NO_OF_THREADS = 10

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) '\
             'AppleWebKit/537.36 (KHTML, like Gecko) '\
             'Chrome/79.0.3945.117 Safari/537.36',


class DevilTeamSpider(scrapy.Spider):
    name = 'devilteam_spider'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://devilteam.pl"
        self.login_url = 'https://devilteam.pl/ucp.php?mode=login'
        self.topic_pattern = re.compile(r't=(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.pagination_pattern = re.compile(r'start=(\d+)')
        self.output_path = kwargs.get("output_path")
        self.avatar_path = kwargs.get("avatar_path")
        self.headers = {
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'user-agent': USER_AGENT,
        }

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.proceed_for_login
        )

    def proceed_for_login(self, response):
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
            url=self.login_url,
            callback=self.parse,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
            )

    def parse(self, response):
        forums = response.xpath(
            '//a[@class="forumtitle"]')
        sub_forums = response.xpath(
            '//div[@class="sub-forumlist"]//li'
            '/a[contains(@href, "viewforum.php?f=")]')
        forums.extend(sub_forums)

        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url.strip('.')
            # if 'f=62' not in url:
            #     continue
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_forum(self, response):
        self.logger.info('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//a[@class="topictitle"]')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url.strip('.')
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

        next_page = response.xpath(
            '//li[@class="arrow next"]/a')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url.strip('.')
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        paginated_value = int(int(pagination[0])/10 + 1) if pagination else 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'{topic_id}-{paginated_value} done..!')

        avatars = response.xpath(
            '//img[@class="avatar"]')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if self.base_url not in avatar_url:
                avatar_url = self.base_url + avatar_url.strip('.')
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

        next_page = response.xpath(
            '//li[@class="arrow next"]/a')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url.strip('.')
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={'topic_id': topic_id}
            )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        file_name_only = file_name.rsplit('.', 1)[0]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            self.logger.info(f"Avatar for {file_name_only} done..!")


class DevilTeamScrapper(SiteMapScrapper):

    spider_class = DevilTeamSpider

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS
            }
        )
        return spider_settings
