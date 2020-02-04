import os
import re
import json
import scrapy
from math import ceil
import configparser
from glob import glob
from lxml.html import fromstring
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from datetime import datetime
from scraper.base_scrapper import BypassCloudfareSpider, SiteMapScrapper

USER = 'cyrax'
PASS = 'Night#Xss007'
REQUEST_DELAY = 0.5
NO_OF_THREADS = 5
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'


class XSSSpider(BypassCloudfareSpider):
    name = 'xss_spider'
    new_posts_url = 'https://xss.is/whats-new/posts/'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://xss.is"
        self.start_url = '{}/forums/'.format(self.base_url)
        self.topic_pattern = re.compile(r'threads/(\d+)/$')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page-(\d+)$')
        self.start_url = 'https://xss.is/'
        self.headers = {
            "user-agent": USER_AGENT
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.parse
        )

    def parse(self, response):
        token = response.xpath(
            '//input[@name="_xfToken"]/@value').extract_first()
        params = {
            'login': USER,
            'password': PASS,
            "remember": '1',
            '_xfRedirect': 'https://xss.is/',
            '_xfToken': token
        }
        yield FormRequest(
            url="https://xss.is/login/login",
            callback=self.parse_main_page,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
            )

    def parse_main_page(self, response):
        if self.start_date:
            yield scrapy.Request(
                url=self.new_posts_url,
                headers=self.headers,
                callback=self.parse_new_posts,
            )
        else:
            forums = response.xpath(
                '//h3[@class="node-title"]/a')
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
        thread_blocks = response.xpath(
            '//div[@class="structItemContainer"]/div')
        for thread_block in thread_blocks:
            # Get topic_id
            topic_id = thread_block.xpath(
                './/a[@data-preview-url]/@href').re(r'threads/(\d+)/')
            if not topic_id:
                continue
            topic_id = topic_id[0]

            # Check thread update time
            thread_date = self.get_thread_date(thread_block)
            if thread_date < self.start_date:
                self.logger.info(
                    f"TopicId {topic_id} ignored "
                    f"because of older udpate: {thread_date}")
                continue

            # Check existing saved paginated files and get  max paginated value
            max_pagination = self.get_latest_pagination(topic_id)
            self.logger.info(
                f"Started downloading of TopicId {topic_id} from "
                f"pagination {max_pagination}")
            thread_url = f'{self.base_url}/threads/{topic_id}/'\
                         f'page-{max_pagination}'

            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={'topic_id': topic_id}
            )
        next_page = response.xpath(
            '//a[@class="pageNav-jump pageNav-jump--next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_new_posts,
            )

    def get_thread_date(self, tag):
        updated_ts = tag.xpath(
            './/time[@class="structItem-latestDate u-dt"]'
            '/@data-time').extract_first()
        return datetime.fromtimestamp(int(updated_ts))

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
                headers=self.headers,
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
            '//div[@class="message-avatar-wrapper"]/a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if self.base_url not in avatar_url:
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
            '//a[@class="pageNav-jump pageNav-jump--next"]')
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
        file_name_only = file_name.rsplit('.', 1)[0]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            self.logger.info(f"Avatar for {file_name_only} done..!")


class XSSScrapper(SiteMapScrapper):

    spider_class = XSSSpider

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
                'HTTPERROR_ALLOWED_CODES': [403],
            }
        )
        return settings
