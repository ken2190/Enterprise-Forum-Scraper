import os
import re
import uuid

from datetime import datetime
from scrapy.utils.gz import gunzip

from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


class YouHackSpider(SitemapSpider):

    name = 'youhack_spider'

    base_url = "https://youhack.ru/"
    sitemap_url = "https://youhack.ru/sitemap.php"

    # Xpath stuffs
    forum_sitemap_xpath = "//sitemap/loc/text()"
    thread_sitemap_xpath = "//url[loc[contains(text(),\"/threads/\")] and lastmod]"
    thread_url_xpath = "//loc/text()"
    thread_lastmod_xpath = "//lastmod/text()"
    forbidden_text_xpath = "//h1/text()[contains(.,\"Forbidden\")]"

    # Regex stuffs
    topic_pattern = re.compile(r'threads/(\d+)')
    avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
    pagination_pattern = re.compile(r'.*page-(\d+)')

    # Other settings
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    handle_httpstatus_list = [403]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": 'none',
                "sec-fetch-user": "?1",
            }
        )

    def parse_thread_date(self, thread_date):
        return datetime.strptime(
            thread_date[:-6],
            self.sitemap_datetime_format
        )

    def parse_sitemap(self, response):

        # Check forbidden
        forbidden_text = response.xpath(
            self.forbidden_text_xpath
        ).extract_first()

        # Process out of forbidden
        if response.status == 403 and forbidden_text:
            self.logger.info(
                "Rotated ip has been forbidden, rotating."
            )
            request = response.request
            request.dont_filter = True
            request.meta["cookiejar"] = uuid.uuid1().hex
            yield request
        else:
            yield from super().parse_sitemap(response)

    def parse_sitemap_forum(self, response):

        # Load selector
        selector = Selector(text=gunzip(response.body))

        # Load thread
        all_threads = selector.xpath(self.thread_sitemap_xpath).extract()

        for thread in all_threads:
            yield from self.parse_sitemap_thread(thread, response)

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

            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_forum(self, response):
        self.logger.info(
            "Next_page_url: %s" % response.request.url
        )

        threads = response.xpath(
            '//ol[@class="discussionListItems"]/li//h3[@class="title"]/a'
        )

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

        next_page_url = response.xpath(
            '//nav/a[text()="Вперёд >"]/@href').extract_first()
        if next_page_url:
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
            yield Request(
                url=avatar_url,
                headers=self.headers,
                callback=self.parse_avatar,
                meta={
                    'file_name': file_name,
                }
            )

        next_page_url = response.xpath(
            '//nav/a[text()="Вперёд >"]/@href').extract_first()
        if next_page_url:
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


class YouHackScrapper(SiteMapScrapper):

    spider_class = YouHackSpider
    request_delay = 0.2
    no_of_threads = 16
    site_name = 'youhack.ru'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': self.request_delay,
                'CONCURRENT_REQUESTS': self.no_of_threads,
                'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads,
            }
        )
        return settings
