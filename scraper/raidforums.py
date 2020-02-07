import os
import re
import sqlite3
import dateutil.parser as dparser
from scrapy.http import Request
from scrapy.crawler import CrawlerProcess
from datetime import datetime
from scrapy import Selector
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 0.3
NO_OF_THREADS = 10


class RaidForumsSpider(SitemapSpider):

    name = 'raidforums_spider'

    # Url stuffs
    base_url = "https://raidforums.com/"
    start_urls = ["https://raidforums.com/"]
    sitemap_url = "https://raidforums.com/sitemap-index.xml"

    # Regex stuffs
    pagination_pattern = re.compile(
        r'.*page=(\d+)',
        re.IGNORECASE
    )
    username_pattern = re.compile(
        r'User-(.*)',
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r'.*/(\S+\.\w+)',
        re.IGNORECASE
    )

    # Xpath stuffs
    forum_sitemap_xpath = "//sitemap[loc[contains(text(),\"sitemap-threads.xml\")]]/loc/text()"
    thread_sitemap_xpath = "//url[loc[contains(text(),\"/Thread-\")] and lastmod]"
    thread_url_xpath = "//loc/text()"
    thread_lastmod_xpath = "//lastmod/text()"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, response):

        forums = response.xpath(
            '//a[contains(@href, "Forum-")]')

        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            yield Request(
                url=url,
                callback=self.parse_forum
            )

    def parse_new_posts(self, response):
        threads = response.xpath(
            '//a[text()="New"]')

        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = self.get_topic_id(thread_url)
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
                callback=self.parse_new_posts
            )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//a[@class="forum-display__thread-name"]')
        if not self.useronly:
            for thread in threads:
                thread_url = thread.xpath('@href').extract_first()
                if self.base_url not in thread_url:
                    thread_url = self.base_url + thread_url
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

        users = response.xpath('//span[@class="author smalltext"]/a')
        for user in users:
            user_url = user.xpath('@href').extract_first()
            if self.base_url not in user_url:
                user_url = self.base_url + user_url
            user_id = self.username_pattern.findall(user_url)
            if not user_id:
                continue
            file_name = '{}/{}.html'.format(self.user_path, user_id[0])
            if os.path.exists(file_name):
                continue
            yield Request(
                url=user_url,
                headers=self.headers,
                callback=self.parse_user,
                meta={
                    'file_name': file_name,
                    'user_id': user_id[0]
                }
            )

        next_page = response.xpath('//a[@class="pagination_next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                # headers=self.headers,
                callback=self.parse_forum
            )

    def parse_user(self, response):
        file_name = response.meta['file_name']
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f"User {response.meta['user_id']} done..!")
        user_history = response.xpath(
            '//span[text()="Username Changes:"]'
            '/following-sibling::a[1]'
        )
        if user_history:
            history_url = user_history.xpath('@href').extract_first()
            if self.base_url not in history_url:
                history_url = self.base_url + history_url
            yield Request(
                url=history_url,
                headers=self.headers,
                callback=self.parse_user_history,
                meta={'user_id': response.meta['user_id']}
            )

    def parse_user_history(self, response):
        user_id = response.meta['user_id']
        file_name = '{}/{}-history.html'.format(self.user_path, user_id)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f"History for user {user_id} done..!")

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']

        pagination = self.pagination_pattern.findall(response.url)
        paginated_value = pagination[0] if pagination else 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f'{topic_id}-{paginated_value} done..!')

        avatars = response.xpath('//a[@class="post__user-avatar"]/img')
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
            '//section[@id="thread-navigation"]//a[@class="pagination_next"]')
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


class RaidForumsScrapper(SiteMapScrapper):

    spider_class = RaidForumsSpider

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


if __name__ == '__main__':
    print("Success!")
