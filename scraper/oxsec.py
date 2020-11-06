import time
import requests
import os
import json
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from scraper.base_scrapper import SiteMapScrapper

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) '\
             'AppleWebKit/537.36 (KHTML, like Gecko) '\
             'Chrome/79.0.3945.117 Safari/537.36',


class Ox00SecSpider(scrapy.Spider):
    name = '0x00sec_spider'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_url = "https://0x00sec.org/latest.json?no_definitions=true&page={}"
        self.base_url = 'https://0x00sec.org/'
        self.thread_url = 'https://0x00sec.org/t/{}/{}'
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.output_path = kwargs.get("output_path")
        self.avatar_path = kwargs.get("avatar_path")
        self.start_page = 0
        self.headers = {
            'sec-fetch-mode': 'same-origin',
            'sec-fetch-site': 'same-origin',
            'user-agent': USER_AGENT
        }

    def start_requests(self):
        url = self.api_url.format(self.start_page)
        yield Request(
            url=url,
            headers=self.headers,
            callback=self.parse_json
        )

    def parse_json(self, response):
        json_data = json.loads(response.text)
        topics = json_data['topic_list']['topics']
        if not topics:
            return
        for topic in topics:
            topic_id = topic['id']
            thread_url = self.thread_url.format(topic['slug'], topic_id)
            file_name = '{}/{}-1.html'.format(self.output_path, topic_id)
            if os.path.exists(file_name):
                continue
            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={'topic_id': topic_id}
            )
        self.start_page += 1
        url = self.api_url.format(self.start_page)
        yield Request(
            url=url,
            headers=self.headers,
            callback=self.parse_json
        )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        paginated_value = 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'{topic_id}-{paginated_value} done..!')
        preloaded_data = response.xpath(
            '//div[@id="data-preloaded"]/@data-preloaded').extract_first()
        json_data = json.loads(preloaded_data)
        participants = json.loads(
            json_data[f'topic_{topic_id}'])['details']['participants']
        for parti in participants:
            avatar_url = parti['avatar_template']
            if not avatar_url:
                continue
            avatar_url = avatar_url.strip('/').replace('{size}', '240')
            if not avatar_url.startswith('http'):
                avatar_url = self.base_url + avatar_url
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

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        file_name_only = file_name.rsplit('.', 1)[0]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            self.logger.info(f"Avatar for {file_name_only} done..!")


class Ox00SecScrapper(SiteMapScrapper):

    request_delay = 0.1
    no_of_threads = 16

    spider_class = Ox00SecSpider
    site_name = '0x00sec.org'
    site_type = 'forum'

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': self.request_delay,
                'CONCURRENT_REQUESTS': self.no_of_threads,
                'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads
            }
        )
        return spider_settings
