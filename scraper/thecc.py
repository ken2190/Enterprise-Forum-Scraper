import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from scraper.base_scrapper import SiteMapScrapper


REQUEST_DELAY = 0.5
NO_OF_THREADS = 16

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) '\
             'AppleWebKit/537.36 (KHTML, like Gecko) '\
             'Chrome/79.0.3945.117 Safari/537.36',


class TheCCSpider(scrapy.Spider):
    name = 'thecc_spider'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.start_url = 'https://thecc.bz/'
        self.output_path = kwargs.get("output_path")
        self.avatar_path = kwargs.get("avatar_path")
        self.pagination_pattern = re.compile(r'/(\d+)/')
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
        forums = response.xpath(
            '//a[@class="subject"]')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            url = url.split('/?PHPSESSID=')[0]
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_forum(self, response):
        self.logger.info('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//td[contains(@class, "subject ")]//span/a')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            thread_url = thread_url.split('/?PHPSESSID=')[0]
            topic_id = str(
                int.from_bytes(
                    thread_url.encode('utf-8'), byteorder='big'
                ) % (10 ** 7)
            )

            file_name = '{}/{}-1.html'.format(self.output_path, topic_id)
            if os.path.exists(file_name):
                continue
            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={'topic_id': topic_id}
            )

        next_page = response.xpath(
            '//div[@class="pagelinks floatleft"]/strong'
            '/following-sibling::a[1][@class="navPages"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        if pagination:
            paginated_value = int(int(pagination[0])/15 + 1)
        else:
            paginated_value = 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'{topic_id}-1 done..!')

        avatars = response.xpath(
            '//div[@class="poster"]//div/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
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
            '//div[@class="pagelinks floatleft"]/strong'
            '/following-sibling::a[1][@class="navPages"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
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


class TheCCScrapper(SiteMapScrapper):

    spider_class = TheCCSpider

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
