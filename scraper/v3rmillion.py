import time
import requests
import os
import re
import scrapy
from glob import glob
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 0.75
NO_OF_THREADS = 5

USER = 'hackwithme123'
PASS = '6VUZmjFzM2WtyjV'

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'


class V3RMillionSpider(SitemapSpider):
    name = 'v3rmillion_spider'
    new_posts_url = 'https://v3rmillion.net/search.php?action=getnew'

    # Other settings
    use_proxy = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = 'https://v3rmillion.net/'
        self.topic_pattern = re.compile(r'tid=(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page=(\d+)')
        self.start_url = 'https://v3rmillion.net/'
        self.headers = {
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'referer': 'https://v3rmillion.net/',
            "user-agent": USER_AGENT
        }

    def start_requests(self):
        formdata = {
            'action': 'do_login',
            'url': '/index.php',
            'username': USER,
            'password': PASS,
            'code': '',
            'remember': 'yes',
            '_challenge': ''
        }
        login_url = 'https://v3rmillion.net/member.php'
        yield FormRequest(
            url=login_url,
            formdata=formdata,
            headers=self.headers,
            callback=self.parse
        )

    def parse(self, response):
        self.headers.update(response.request.headers)
        if self.start_date:
            yield scrapy.Request(
                url=self.new_posts_url,
                headers=self.headers,
                callback=self.parse_new_posts,
            )
        else:
            forums = response.xpath(
                '//td[@class="trow1" or @class="trow2"]/strong'
                '/a[contains(@href, "forumdisplay.php?fid=")]')
            subforums = response.xpath(
                '//span[@class="sub_control"]'
                '/a[contains(@href, "forumdisplay.php?fid=")]')
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

    def parse_new_posts(self, response):
        topics = response.xpath(
            '//a[contains(@href, "showthread.php?tid=") '
            'and contains(@id, "tid_")]')
        for topic in topics:
            # Get thread url
            thread_url = topic.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = f'{self.base_url}{thread_url}'

            # Get topic id
            match = self.topic_pattern.findall(thread_url)
            if not match:
                continue
            topic_id = match[0]

            # Check existing saved paginated files and get  max paginated value
            max_pagination = self.get_latest_pagination(topic_id)
            self.logger.info(
                f"Started downloading of TopicId {topic_id} from "
                f"pagination {max_pagination}")
            thread_url = f'{thread_url}&page={max_pagination}'
            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={'topic_id': topic_id}
            )
        next_page = response.xpath('//a[@class="pagination_next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_new_posts,
            )

    def get_latest_pagination(self, topic_id):
        pagination_pattern = re.compile(r'\d+-(\d+)')
        existing_paginations = [
            int(pagination_pattern.search(x).group(1))
            for x in glob(f'{self.output_path}/{topic_id}-*.html')
        ]
        return max(existing_paginations) if existing_paginations else 1

    def parse_forum(self, response):
        self.logger.info('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//span[contains(@id, "tid_")]'
            '/a[contains(@href, "showthread.php?tid=")]')
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

        next_page = response.xpath('//a[@class="pagination_next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
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

        avatars = response.xpath('//div[@class="author_avatar"]/a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
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

        next_page = response.xpath(
            '//div[@class="pagination"]'
            '/a[@class="pagination_next"]')
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


class V3RMillionScrapper(SiteMapScrapper):
    spider_class = V3RMillionSpider

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
