import re
import uuid

from datetime import datetime, timedelta
from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


class MfdSpider(SitemapSpider):
    name = 'mfd_spider'

    # Url stuffs
    base_url = "http://forum.mfd.ru"

    # Xpath stuffs
    forum_xpath = '//a[contains(@href, "/forum/subforum")]/@href'
    thread_xpath = '//table[@class="mfd-table mfd-threads"]//tr[td]'
    thread_first_page_xpath = './/a[contains(@href,"forum/thread/?id=")]/@href'
    thread_last_page_xpath = './/a[contains(@href,"forum/thread/?id=")]/@href'
    thread_date_xpath = './/td[@class="mfd-item-lastpost"]/a/text()'
    pagination_xpath = '//div[@class="mfd-paginator"]'\
                       '/a[@class="mfd-paginator-selected"]'\
                       '/following-sibling::a[1]/@href'
    thread_pagination_xpath = '//div[@class="mfd-paginator"]'\
                              '/a[@class="mfd-paginator-selected"]'\
                              '/preceding-sibling::a[1]/@href'
    thread_page_xpath = '//div[@class="mfd-paginator"]'\
                        '/a[@class="mfd-paginator-selected"]/text()'
    post_date_xpath = '//a[@class="mfd-post-link"]/text()'

    avatar_xpath = '//div[@class="mfd-post-avatar"]/a/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"thread/\?id=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "On"
    sitemap_datetime_format = '%d.%m.%Y'
    post_datetime_format = '%d.%m.%Y %H:%M'

    def start_requests(self):
        yield Request(
            url=f'{self.base_url}/forum/',
            headers=self.headers,
        )

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        thread_date = thread_date.split(',')[0].strip()

        if 'сегодня' in thread_date.lower():
            return datetime.today()
        elif "вчера" in thread_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        post_date = post_date.strip()

        if "сегодня" in post_date.lower():
            return datetime.today()
        elif "вчера" in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def parse(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)
        # self.logger.info(response.text)
        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", len(all_forums))

        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url

            yield Request(
                url=forum_url,
                headers=self.headers,
                meta=self.synchronize_meta(response),
                callback=self.parse_forum
            )

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class MfdScrapper(SiteMapScrapper):

    spider_class = MfdSpider
    site_name = 'forum.mfd.ru'
    site_type = 'forum'

    def load_settings(self):
        spider_settings = super().load_settings()
        return spider_settings
