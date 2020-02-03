import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy import Selector
from datetime import datetime
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'
REQUEST_DELAY = 0.2
NO_OF_THREADS = 10


class SkyFraudSpider(SitemapSpider):
    name = 'skyfraud_spider'
    sitemap_url = 'https://sky-fraud.ru/sitemap_forum_1.xml.gz'
    # Xpath stuffs
    thread_xpath = '//url[loc[contains(text(),"/showthread.php")] and lastmod]'
    thread_url_xpath = "//loc/text()"
    thread_date_xpath = "//lastmod/text()"
    sitemap_datetime_format = '%Y-%m-%dT%H:%M:%S'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://sky-fraud.ru/"
        self.topic_pattern = re.compile(r'.*t=(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'&page=(\d+)')
        self.start_url = self.base_url
        self.headers = {
            "user-agent": USER_AGENT
        }

    def parse_sitemap(self, response):
        # Load selector
        selector = Selector(text=response.text)

        # Load forum
        all_threads = selector.xpath(self.thread_xpath).extract()

        for thread in all_threads:
            yield from self.parse_sitemap_thread(thread)

    def parse_thread_date(self, thread_date):
        return datetime.strptime(
            thread_date.split('+')[0],
            self.sitemap_datetime_format
        )

    def parse(self, response):
        forums = response.xpath(
            '//a[contains(@href, "forumdisplay.php?")]')
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
            '//a[contains(@id, "thread_title_")]')
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

        next_page = response.xpath('//a[@rel="next"]')
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

        avatars = response.xpath('//a[contains(@href, "member.php?")]/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if 'image/svg' in avatar_url:
                continue
            name_match = self.avatar_name_pattern.findall(avatar_url)
            if not name_match:
                continue
            if self.base_url not in avatar_url:
                avatar_url = self.base_url + avatar_url
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

        next_page = response.xpath('//a[@rel="next"]')
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


class SkyFraudScrapper(SiteMapScrapper):

    spider_class = SkyFraudSpider

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
