import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.crawler import CrawlerProcess
from datetime import datetime

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)
from scrapy import (
    Request,
    FormRequest
)


class XrpChatSpider(SitemapSpider):

    name = 'xrpchat_spider'

    # Url stuffs
    base_url = "https://www.xrpchat.com/"
    start_urls = ["https://www.xrpchat.com/"]
    sitemap_url = "https://www.xrpchat.com/sitemap.php"

    # Regex stuffs
    topic_pattern = re.compile(
        r'topic/(\d+)-',
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r'.*/(\S+\.\w+)',
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r'.*/page/(\d+)/',
        re.IGNORECASE
    )

    # Xpath stuffs
    forum_xpath = "//sitemap[loc[contains(text(),\"content_forums\")]]/loc/text()"
    thread_xpath = "//url[loc[contains(text(),\"/topic/\")] and lastmod]"
    thread_url_xpath = "//loc/text()"
    thread_date_xpath = "//lastmod/text()"

    # Other settings
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"

    def get_topic_id(self, url=None):
        topic_id = self.topic_pattern.findall(url)
        if not topic_id:
            return
        return topic_id[0]

    def parse_thread_date(self, thread_date):
        return datetime.strptime(
            thread_date[:-6],
            self.sitemap_datetime_format
        )

    def parse(self, response):
        forums = response.xpath(
            '//div[@class="ipsDataItem_main"]//h4'
            '/a[contains(@href, "forum/")]')
        sub_forums = response.xpath(
            '//div[@class="ipsDataItem_main"]/ul/li'
            '/a[contains(@href, "forum/")]')
        forums.extend(sub_forums)
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            # if '/38-services/' not in url:
            #     continue
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//div[@class="ipsDataItem_main"]/h4//a')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = self.get_topic_id(thread_url)
            if not topic_id:
                continue
            file_name = '{}/{}-1.html'.format(self.output_path, topic_id)
            if os.path.exists(file_name):
                continue
            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={'topic_id': topic_id}
            )

        next_page = response.xpath('//li[@class="ipsPagination_next"]/a')
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
            print(f'{topic_id}-{paginated_value} done..!')

        avatars = response.xpath('//li[@class="cAuthorPane_photo"]/a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if avatar_url.startswith('//'):
                avatar_url = 'https:' + avatar_url
            elif not avatar_url.startswith('http'):
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

        next_page = response.xpath('//li[@class="ipsPagination_next"]/a')
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
            print(f"Avatar {file_name_only} done..!")


class XrpChatScrapper(SiteMapScrapper):

    request_delay = 0.1
    no_of_threads = 16
    spider_class = XrpChatSpider

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': self.request_delay,
                'CONCURRENT_REQUESTS': self.no_of_threads,
                'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads,
            }
        )
