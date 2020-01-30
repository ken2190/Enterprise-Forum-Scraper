import os
import re
import json
import scrapy
from math import ceil
import configparser
from lxml.html import fromstring
from urllib.parse import urlencode
from scrapy.http import Request, FormRequest
from scrapy import Selector
from scrapy.utils.gz import gunzip
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper

USER = 'vrx9'
PASS = 'Night#Pro000'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'
REQUEST_DELAY = 1
NO_OF_THREADS = 10


class ProLogicSpider(SitemapSpider):
    name = 'prologic_spider'
    sitemap_url = 'https://prologic.su/sitemap.xml'
    # Xpath stuffs
    forum_xpath = '//sitemap/loc[contains(text(), "sitemap_topics.xml")]/text()'
    thread_xpath = '//url[loc[contains(text(),"/topic/")] and lastmod]'
    thread_url_xpath = "//loc/text()"
    thread_date_xpath = "//lastmod/text()"
    sitemap_datetime_format = "%Y-%m-%d"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://prologic.su/"
        self.topic_pattern = re.compile(r'/topic/(\d+)-')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page__st__(\d+)$')
        self.start_url = 'https://prologic.su/'
        self.headers = {
            "user-agent": USER_AGENT,
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.proceed_for_login
        )

    def proceed_for_login(self, response):
        auth_key = response.xpath(
            '//input[@name="auth_key"]/@value').extract_first()
        params = {
            'auth_key': auth_key,
            'referer': 'https://prologic.su/',
            'ips_username': USER,
            'ips_password': PASS,
            "rememberMe": '1',
        }
        login_url = 'https://prologic.su/index.php?app=core&module=global'\
                    '&section=login&do=process'
        yield FormRequest(
            url=login_url,
            callback=self.parse_main_page,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
            )

    def parse_main_page(self, response):
        if self.start_date:
            yield scrapy.Request(
                url=self.sitemap_url,
                headers=self.headers,
                callback=self.parse_sitemap
            )
        else:
            forums = response.xpath(
                '//h4[@class="forum_name"]/strong/a')
            subforums = response.xpath(
                '//ol[contains(@id, "subforums_")]/li/a')
            forums.extend(subforums)
            for forum in forums:
                url = forum.xpath('@href').extract_first()
                if self.base_url not in url:
                    url = self.base_url + url
                # if not url.endswith('2-microsoft-windows/'):
                #     continue
                yield Request(
                    url=url,
                    headers=self.headers,
                    callback=self.parse_forum
                )

    def parse_sitemap_forum(self, response):

        # Load selector
        text = gunzip(response.body)
        selector = Selector(text=gunzip(response.body))

        # Load thread
        all_threads = selector.xpath(self.thread_xpath).extract()
        for thread in all_threads:
            yield from self.parse_sitemap_thread(thread)

    def parse_forum(self, response):
        self.logger.info('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//a[contains(@id, "tid-link-")]')
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
            '//a[@rel="next"]')
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
        paginated_value = int(pagination[0])//25 + 1 if pagination else 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'{topic_id}-{paginated_value} done..!')

        avatars = response.xpath('//li[@class="avatar"]/a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if self.base_url not in avatar_url:
                avatar_url = self.base_url + avatar_url
            match = self.avatar_name_pattern.findall(avatar_url)
            if not match:
                continue
            file_name = '{}/{}.jpg'.format(self.avatar_path, match[0])
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
            '//a[@rel="next"]')
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


class ProLogicScrapper(SiteMapScrapper):

    spider_class = ProLogicSpider

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
