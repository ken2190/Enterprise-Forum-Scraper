import os
import re
import scrapy
import uuid

from scrapy.http import Request, FormRequest
from scraper.base_scrapper import (
    BypassCloudfareSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 0.3
NO_OF_THREADS = 3
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'


class CrackCommunitySpider(BypassCloudfareSpider):
    name = 'crackcommunity_spider'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = 'http://crackcommunity.com/'
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.topic_pattern = re.compile(r'threads/.*\.(\d+)/')
        self.pagination_pattern = re.compile(r'.*page-(\d+)')

    def start_requests(self):
        yield Request(
            url=self.base_url,
            callback=self.parse,
            headers={
                'User-Agent': USER_AGENT,
                'Host': 'crackcommunity.com'
            }
        )

    def parse(self, response):
        forums = response.xpath(
            '//ol[@class="nodeList"]//h3[@class="nodeTitle"]'
            '/a[contains(@href, "forums/")]')
        subforums = response.xpath(
            '//ol[@class="subForumList"]//h4[@class="nodeTitle"]'
            '/a[contains(@href, "forums/")]')
        forums.extend(subforums)
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            # if 'sellers-area.22/' not in url:
            #     continue
            yield Request(
                url=url,
                callback=self.parse_forum,
                headers=response.request.headers,
                meta=response.meta
            )

    def parse_forum(self, response):
        self.logger.info("Next_page_url: %s" % response.request.url)

        threads = response.xpath(
            '//ol[@class="discussionListItems"]/li'
            '//h3[@class="title"]/a'
        )

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
            meta = response.meta
            meta.update({'topic_id': topic_id[0]})
            yield Request(
                url=thread_url,
                headers=response.request.headers,
                callback=self.parse_thread,
                meta=meta,
            )

        next_page_url = response.xpath(
            '//nav/a[text()="Next"]/@href').extract_first()
        if next_page_url:
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=response.request.headers,
                callback=self.parse_forum,
                meta=response.meta
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

        avatars = response.xpath(
            '//div[@class="avatarHolder"]/a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if not avatar_url:
                continue
            if self.base_url not in avatar_url:
                avatar_url = self.base_url + avatar_url
            name_match = self.avatar_name_pattern.findall(avatar_url)
            if not name_match:
                continue
            name = name_match[0]
            file_name = '{}/{}'.format(self.avatar_path, name)
            if os.path.exists(file_name):
                continue
            meta = response.meta
            meta.update({'file_name': file_name})
            yield Request(
                url=avatar_url,
                headers=response.request.headers,
                callback=self.parse_avatar,
                meta=meta
            )
        meta = response.meta
        meta.update({'topic_id': topic_id})
        next_page_url = response.xpath(
            '//nav/a[text()="Next"]/@href').extract_first()
        if next_page_url:
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=response.request.headers,
                callback=self.parse_thread,
                meta=meta
            )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        file_name_only = file_name.rsplit('/', 1)[-1]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            print(f"Avatar {file_name_only} done..!")


class CrackCommunityScrapper(SiteMapScrapper):

    spider_class = CrackCommunitySpider
    site_name = 'crackcommunity.com'

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
            }
        )
        return spider_settings
