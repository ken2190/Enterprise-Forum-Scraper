import os
import re
import scrapy
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


REQUEST_DELAY = 1
NO_OF_THREADS = 1

USERNAME = "Cyrax_011"
PASSWORD = "Night#India065"


class DevilTeamSpider(SitemapSpider):
    name = 'devilteam_spider'
    base_url = "https://devilteam.pl"

    # xpaths
    login_form_xpath = '//form[@method="post"]'
    forum_xpath = '//a[contains(@class, "forumtitle")]/@href'

    pagination_xpath = '//li[@class="arrow next"]/a/@href'

    thread_xpath = '//ul[@class="topiclist topics"]/li'
    thread_first_page_xpath = './/a[contains(@class, "topictitle")]/@href'
    thread_last_page_xpath = './/div[@class="pagination"]'\
                             '/ul/li[last()]/a/@href'
    thread_date_xpath = './/dd[@class="lastpost"]/span/time/@datetime'
    thread_page_xpath = '//li[contains(@class, "ipsPagination_active")]'\
                        '/a/text()'
    thread_pagination_xpath = '//li[@class="arrow previous"]'\
                              '/a[@rel="prev"]/@href'

    post_date_xpath = '//p[@class="author"]//time/@datetime'

    avatar_xpath = '//span[@class="avatar"]/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"&t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r'.*/(\S+\.\w+)',
        re.IGNORECASE
    )

    # Other settings
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    use_proxy = True

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse_start
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        creation_time = response.xpath(
            '//input[@name="creation_time"]/@value').extract_first()
        form_token = response.xpath(
            '//input[@name="form_token"]/@value').extract_first()
        sid = response.xpath(
            '//input[@name="sid"]/@value').extract_first()
        formdata = {
            'username': USERNAME,
            'password': PASSWORD,
        }
        self.logger.info(formdata)
        yield FormRequest.from_response(
            response,
            formxpath=self.login_form_xpath,
            formdata=formdata,
            meta=self.synchronize_meta(response),
            dont_filter=True,
            headers=self.headers
        )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class DevilTeamScrapper(SiteMapScrapper):

    spider_class = DevilTeamSpider
    site_name = 'devilteam.pl'
