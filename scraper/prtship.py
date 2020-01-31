import os
import re
import json
import scrapy
from math import ceil
import configparser
from lxml.html import fromstring
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess


class PrtShipSpider(SitemapSpider):
    name = 'prtship_spider'
    sitemap_url = 'https://prtship.com/sitemap.xml'
    # Xpath stuffs
    forum_xpath = '//sitemap/loc[contains(text(), "sitemap_topics.xml")]/text()'
    thread_xpath = '//url[loc[contains(text(),"/topic/")] and lastmod]'
    thread_url_xpath = "//loc/text()"
    thread_date_xpath = "//lastmod/text()"
    sitemap_datetime_format = "%Y-%m-%d"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base_url = "https://prtship.com"
        self.start_url = '{}/forums/'.format(self.base_url)
        self.topic_pattern = re.compile(r'.*\.(\d+)/$')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page-(\d+)$')
        self.start_url = 'https://prtship.com'
        self.output_path = output_path
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/74.0.3729.169 Safari/537.36",
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
            '_xfRequestUri': '/',
            '_xfWithData': '1',
            '_xfToken': token,
            '_xfResponseType': 'json'
        }
        yield FormRequest(
            url="https://prtship.com/list-custom-tabs/english.1",
            callback=self.parse_main_page,
            formdata=params,
            headers=self.headers
            )

    def parse_sitemap_forum(self, response):

        # Load selector
        text = gunzip(response.body)
        selector = Selector(text=gunzip(response.body))

        # Load thread
        all_threads = selector.xpath(self.thread_xpath).extract()
        for thread in all_threads:
            yield from self.parse_sitemap_thread(thread)

    def parse_main_page(self, response):
        if self.start_date:
            yield scrapy.Request(
                url=self.sitemap_url,
                headers=self.headers,
                callback=self.parse_sitemap
            )

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
        file_name_only = file_name.rsplit('/', 1)[-1]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            self.logger.info(f"Avatar {file_name_only} done..!")


class PrtShipScrapper(SiteMapScrapper):

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
