import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from scraper.base_scrapper import SiteMapScrapper

REQUEST_DELAY = 0.1
NO_OF_THREADS = 16

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) '\
             'AppleWebKit/537.36 (KHTML, like Gecko) '\
             'Chrome/79.0.3945.117 Safari/537.36',


class HackThisSiteSpider(scrapy.Spider):
    name = 'hackthissite_spider'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "http://hackthissite.org/forums"
        self.start_url = "http://hackthissite.org/forums/index.php"
        self.topic_pattern = re.compile(r'.*t=(\d+)')
        self.avatar_name_pattern = re.compile(r'.*id=(.*)')
        self.pagination_pattern = re.compile(r'.*start=(\d+)$')
        self.output_path = kwargs.get("output_path")
        self.avatar_path = kwargs.get("avatar_path")
        self.headers = {
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'user-agent': USER_AGENT
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            callback=self.parse,
            headers=self.headers,
        )

    def parse(self, response):
        forums = response.xpath(
            '//a[@class="forumtitle" or @class="subforum read"]')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url.strip('.')
            if 'f=41' not in url:
                continue
            yield Request(
                url=url,
                callback=self.parse_forum,
                headers=self.headers,
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
                callback=self.parse_thread,
                meta={'topic_id': topic_id[0]},
                headers=self.headers,
            )

        next_page = response.xpath('//a[text()="Next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url.strip('.')
            yield Request(
                url=next_page_url,
                callback=self.parse_forum,
                headers=self.headers,
            )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        if pagination:
            paginated_value = int(int(pagination[0])/10 + 1)
        else:
            paginated_value = 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'{topic_id}-{paginated_value} done..!')

        avatars = response.xpath('//img[@alt="User avatar"]')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if not avatar_url:
                continue
            avatar_url = self.base_url + avatar_url.strip('.')\
                if not avatar_url.startswith('http') else avatar_url
            match = self.avatar_name_pattern.findall(avatar_url)
            if not match:
                continue
            if '.' in match[0]:
                file_name = '{}/{}'.format(self.avatar_path, match[0])
            else:
                file_name = '{}/{}.jpg'.format(self.avatar_path, match[0])
            if os.path.exists(file_name):
                continue
            yield Request(
                url=avatar_url,
                callback=self.parse_avatar,
                meta={
                    'file_name': file_name,
                }
            )

        next_page = response.xpath('//a[text()="Next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url.strip('.')
            yield Request(
                url=next_page_url,
                callback=self.parse_thread,
                meta={'topic_id': topic_id},
                headers=self.headers,
            )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        file_name_only = file_name.rsplit('/', 1)[-1]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            self.logger.info(f"Avatar {file_name_only} done..!")


class HackThisSiteScrapper(SiteMapScrapper):

    spider_class = HackThisSiteSpider
    site_name = 'hackthissite.org'

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
