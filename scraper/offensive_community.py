import os
import re

from scrapy.http import Request
from scrapy.exceptions import CloseSpider
from datetime import datetime
import dateparser

from .base_scrapper import SitemapSpider, SiteMapScrapper


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class OffensiveCommunitySpider(SitemapSpider):
    name = 'offensive_community_spider'
    base_url = 'http://offensivecommunity.net/'

    # Xpaths
    forum_xpath = '//div[@id="content"]/table/tbody/tr//strong/a/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[@class="pagination_next"]/@href'
    thread_xpath = '//table//tr[td[contains(@class,"forum")]]'
    thread_first_page_xpath = '//td[contains(@class,"trow")]/div/span/a[contains(@class,"subject_new")]/@href'

    thread_last_page_xpath = '//td[contains(@class,"trow")]/div/span/span[@class="smalltext"]/a[last()]/@href'

    thread_date_xpath = '//span[contains(@class,"lastpost")]/span/@title'

    thread_pagination_xpath = '//a[@class="pagination_next"]/@href'

    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//td[@class="tcat"]//span/@title|//td[@class="tcat"]/div/text()'

    avatar_xpath = '//td[contains(@class,"post_avatar")]//img/@src'

    topic_pattern = re.compile(
        r".*tid=(\d+)",
        re.IGNORECASE
    )

    avatar_name_pattern = re.compile(
        r"./avatar_(\d+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = '%d-%m-%Y'
    post_datetime_format = '%d-%m-%Y'

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:
            if not 'fid=12' in forum_url:
                pass

            full_url = self.base_url + forum_url
            yield Request(
                url=full_url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def get_forum_next_page(self, response):
        pass

    def parse_thread(self, response):

        # Load all post date
        yield from super().parse_thread(response)

        yield from super().parse_avatars(response)


    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """

        # print('------------Thread date ')
        # print(thread_date)

        if thread_date is None:
            return datetime.today()

        thread_date = thread_date.split(',')[0]
        return dateparser.parse(thread_date)

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """

        if post_date is None:
            return datetime.today()

        return dateparser.parse(post_date)

class OffensiveCommunityScrapper(SiteMapScrapper):
    spider_class = OffensiveCommunitySpider
