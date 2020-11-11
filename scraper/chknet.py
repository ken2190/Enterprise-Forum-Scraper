import re
import scrapy
from math import ceil
import configparser
from urllib.parse import urlencode
from lxml.html import fromstring
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from datetime import datetime
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 0.3
NO_OF_THREADS = 10


USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) '\
             'AppleWebKit/537.36 (KHTML, like Gecko) '\
             'Chrome/79.0.3945.117 Safari/537.36',


class ChkNetSpider(SitemapSpider):
    name = 'chknet_spider'
    base_url = 'https://chknet.is/'

    # Xpaths
    forum_xpath = '//a[contains(@href, "viewforum.php")]/@href'
    thread_xpath = '//ul[@class="topiclist topics"]/li'
    thread_first_page_xpath = './/a[@class="topictitle"]/@href'
    thread_last_page_xpath = './/div[@class="pagination"]'\
                             '/ul/li[last()]/a/@href'
    thread_date_xpath = './/dd[@class="lastpost"]/span/text()[last()]'
    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//div[@class="pagination"]//'\
                        'li[@class="active"]/span/text()'
    post_date_xpath = '//p[@class="author"]/text()[last()]'

    avatar_xpath = '//div[@class="avatar-container"]/img/@src'

    # Other settings
    sitemap_datetime_format = '%a %b %d, %Y %I:%M %p'
    post_datetime_format = '%a %b %d, %Y %I:%M %p'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.topic_pattern = re.compile(r't=(\d+)')
        self.avatar_name_pattern = re.compile(r'avatar=(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'start=(\d+)')
        self.headers = {
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'user-agent': USER_AGENT
        }

    def parse(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        for forum_url in all_forums:

            yield Request(
                url=response.urljoin(forum_url),
                headers=self.headers,
                meta=self.synchronize_meta(response),
                callback=self.parse_forum
            )

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class ChkNetScrapper(SiteMapScrapper):

    spider_class = ChkNetSpider
    site_name = 'chknet.cc'
    site_type = 'forum'
