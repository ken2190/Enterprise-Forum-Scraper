import re
import uuid

from datetime import datetime
from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


<<<<<<< HEAD
REQUEST_DELAY = 0.3
NO_OF_THREADS = 8

USER = "Cyrax0111"
=======
USER = "Cyrax011"
>>>>>>> df60255be9b7aafbba28c8972c29ac0bcc8bc0ae
PASS = "4hr63yh38a61SDW0"


class MalvultSpider(SitemapSpider):
    name = 'malvult_spider'

    # Url stuffs
    base_url = "https://malvult.net/"

    # Xpath stuffs
    forum_xpath = '//h3[@class="nodeTitle"]/a[contains(@href, "forums/")]/@href'
    thread_xpath = '//ol[@class="discussionListItems"]/li'
    thread_first_page_xpath = './/h3[@class="title"]'\
                              '/a[contains(@href,"threads/")]/@href'
    thread_last_page_xpath = './/span[@class="itemPageNav"]'\
                             '/a[last()]/@href'
    thread_date_xpath = './/dl[@class="lastPostInfo"]'\
                        '//a[@class="dateTime"]/abbr/@data-datestring|'\
                        './/dl[@class="lastPostInfo"]'\
                        '//a[@class="dateTime"]/span/text()'
    pagination_xpath = '//nav/a[last()]/@href'
    thread_pagination_xpath = '//nav/a[@class="text"]/@href'
    thread_page_xpath = '//nav//a[contains(@class, "currentPage")]'\
                        '/text()'
    post_date_xpath = '//div[@class="messageDetails"]'\
                      '//span[@class="DateTime"]/text()|'\
                      '//div[@class="messageDetails"]'\
                      '//abbr[@class="DateTime"]/@data-datestring'

    avatar_xpath = '//div[@class="uix_avatarHolderInner"]/a/img/@src'

    # Login Failed Message
    login_failed_xpath = '//div[@class="errorPanel"]'

    # Regex stuffs
    topic_pattern = re.compile(
        r"threads/.*\.(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    sitemap_datetime_format = '%b %d, %Y'
    post_datetime_format = '%b %d, %Y'

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.proceed_for_login,
        )

    def proceed_for_login(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        params = {
            'login': USER,
            'register': '0',
            'password': PASS,
            'remember': '1',
            'cookie_check': '1',
            '_xfToken': '',
            'redirect': 'https://malvult.net/index.php'
        }
        yield FormRequest(
            url="https://malvult.net/index.php?login/login",
            callback=self.parse,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
        )

    def parse(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Check if login failed
        self.check_if_logged_in(response)

        # self.logger.info(response.text)
        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("forum/forum_count", len(all_forums))

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


class MalvultScrapper(SiteMapScrapper):

    spider_class = MalvultSpider
    site_name = 'malvult.net'
    site_type = 'forum'

    def load_settings(self):
        spider_settings = super().load_settings()
        return spider_settings
