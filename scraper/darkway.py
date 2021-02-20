import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


USERNAME = "Cyrax011"
PASSWORD = "4hr63yh38a61SDW0"

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'

PROXY = 'http://127.0.0.1:8118'


class DarkWaySpider(SitemapSpider):
    name = 'darkway_spider'
    base_url = 'http://kzx2d7tcvfm5j6yt2ii7ejkeal3d5oy5gsewwnw7hmywj3nordbg4syd.onion/'

    # Xpaths
    pagination_xpath = '//div[@class="boardFooter"]'\
                       '/text()[contains(.,"[")]'\
                       '/following-sibling::a[1]/@href'
    thread_xpath = '//div[contains(@class, "topicEntry")]'
    thread_first_page_xpath = './/a[contains(@href, "?topic=")]/@href'
    thread_date_xpath = './/div[@class="topicDate"]/text()[last()]'
    thread_pagination_xpath = '//header[@class="topicHeader"]'\
                              '/text()[contains(.,"[")]'\
                              '/following-sibling::a[1]/@href'
    thread_page_xpath = '//header[@class="topicHeader"]/text()[contains(.,"[")]'
    post_date_xpath = '//div[@class="postUser"]/time[@datetime]/@datetime'

    avatar_xpath = '//div[@class="postUser"]/img[@class="avatar"]/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"topic=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r"user=(\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "Tor"
    post_datetime_format = '%Y-%m-%dT%H:%M:%S'
    sitemap_datetime_format = 'on %B %d, %Y %H:%M:%S'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update({
            "user-agent": USER_AGENT
        })

    def start_requests(self):
        yield Request(
            url=f'{self.base_url}?action=login',
            callback=self.proceed_for_login,
            headers=self.headers,
            meta={
                'proxy': PROXY
            }
        )

    def proceed_for_login(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        formdata = {
            'username': USERNAME,
            'password': PASSWORD,
            'loggingin': 'true'
        }
        yield FormRequest(
            url=f'{self.base_url}?action=login',
            formdata=formdata,
            callback=self.parse_forum,
            dont_filter=True,
            headers=self.headers,
            meta=self.synchronize_meta(response)
        )

    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip"]
            if response.meta.get(key)
        }

        meta.update(default_meta)
        meta.update({'proxy': PROXY})

        return meta

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        return datetime.strptime(
            post_date.strip()[:-6],
            self.post_datetime_format
        )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)

    def get_forum_next_page(self, response):
        next_page = response.xpath(self.pagination_xpath).extract_first()
        if not next_page:
            return
        next_page = next_page.strip().strip('.')
        if self.base_url not in next_page:
            next_page = self.base_url + next_page
        return next_page

    def get_thread_next_page(self, response):
        next_page = response.xpath(self.thread_pagination_xpath).extract_first()
        if not next_page:
            return
        next_page = next_page.strip().strip('.')
        if self.base_url not in next_page:
            next_page = self.base_url + next_page
        return next_page

    def get_thread_current_page(self, response):
        current_page = response.xpath(
                self.thread_page_xpath
        ).re(r'\[(\d+)\]')
        if not current_page:
            return '1'
        return current_page[0]

    def parse_thread_url(self, thread_url):
        """
        :param thread_url: str => thread url as string
        :return: str => thread url as string
        """
        if thread_url:
            return thread_url.strip().strip('.')
        else:
            return

    def get_avatar_file(self, url=None):
        """
        :param url: str => avatar url
        :return: str => extracted avatar file from avatar url
        """
        try:
            match = self.avatar_name_pattern.findall(url)
            file_name = '{}/{}.jpg'.format(self.avatar_path, match[0])
            return file_name
        except Exception as err:
            return


class DarkWayScrapper(SiteMapScrapper):

    spider_class = DarkWaySpider
    site_name = 'darkway_kzx2d7tcvfm5j6yt2ii7ejkeal3d5oy5gsewwnw7hmywj3nordbg4syd'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings
