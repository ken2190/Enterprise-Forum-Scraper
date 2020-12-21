import os
import re

from datetime import datetime

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)
from scrapy import (
    Request,
    FormRequest
)

class SkyFraudSpider(SitemapSpider):

    name = "skyfraud_spider"
    sitemap_url = "https://sky-fraud.ru/sitemap_forum_1.xml.gz"
    base_url = "https://sky-fraud.ru/"
    
    # Xpath stuffs
    thread_sitemap_xpath = "//url[loc[contains(text(),\"/showthread.php\")] and lastmod]"
    thread_url_xpath = "//loc/text()"
    thread_lastmod_xpath = "//lastmod/text()"
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"

    # Regex stuffs
    topic_pattern = re.compile(
        r".*t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r"&page=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True

    def parse_thread_date(self, thread_date):
        return datetime.strptime(
            thread_date.split('+')[0],
            self.sitemap_datetime_format
        )

    def parse_sitemap(self, response):
        yield from self.parse_sitemap_forum(response)

    def parse(self, response):

        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        forums = response.xpath(
            '//a[contains(@href, "forumdisplay.php?")]')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_forum(self, response):
        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        self.logger.info('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//a[contains(@id, "thread_title_")]')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url

            # Get topic id
            topic_id = self.get_topic_id(thread_url)
            if not topic_id:
                continue

            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "topic_id": topic_id
                    }
                )
            )

        # Pagination
        next_page = response.xpath("//a[@rel=\"next\"]")
        if next_page:
            next_page_url = next_page.xpath("@href").extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):

        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Load topic id
        topic_id = response.meta.get("topic_id")

        # Save thread content
        pagination = self.pagination_pattern.findall(response.url)
        paginated_value = pagination[0] if pagination else 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'{topic_id}-{paginated_value} done..!')

        # Save avatar content
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
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "file_name": file_name
                    }
                )
            )

        # Thread pagination
        next_page = response.xpath("//a[@rel=\"next\"]")
        if next_page:
            next_page_url = next_page.xpath("@href").extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "topic_id": topic_id
                    }
                )
            )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        file_name_only = file_name.rsplit('/', 1)[-1]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            self.logger.info(f"Avatar {file_name_only} done..!")


class SkyFraudScrapper(SiteMapScrapper):

    spider_class = SkyFraudSpider
    site_name = 'sky-fraud.ru'
    site_type = 'forum'