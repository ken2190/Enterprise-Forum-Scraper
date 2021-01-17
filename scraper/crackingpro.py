import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from datetime import datetime
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper

class CrackingProSpider(SitemapSpider):
    name = 'crackingpro_spider'
    base_url = "https://www.crackingpro.com/"

    # xpaths
    login_form_xpath = '//form[@method="post"]'
    forum_xpath = '//div[@class="lkForumRow_main"]//h4/a/@href|'\
                  '//div[@class="lkForumRow_main"]/ul/li'\
                  '/a[contains(@href, "/forum/")]/@href'

    pagination_xpath = '//li[@class="ipsPagination_next"]/a/@href'

    thread_xpath = '//li[contains(@class, "ipsDataItem ")]'
    thread_first_page_xpath = './/span[@class="ipsType_break ipsContained"]'\
                              '/a/@href'
    thread_last_page_xpath = './/span[@class="ipsPagination_page"][last()]'\
                             '/a/@href'

    thread_date_xpath = './/li[@class="ipsType_light"]/a/time/@datetime'
    thread_page_xpath = '//li[contains(@class, "ipsPagination_active")]'\
                        '/a/text()'
    thread_pagination_xpath = '//li[@class="ipsPagination_prev"]'\
                              '/a/@href'

    post_date_xpath = '//a/time[@datetime]/@datetime'

    avatar_xpath = '//li[@class="cAuthorPane_photo"]//a/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r'topic/(\d+)-',
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r'.*/(\S+\.\w+)',
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "On"
    sitemap_datetime_format = '%Y-%m-%dT%H:%M:%SZ'
    post_datetime_format = '%Y-%m-%dT%H:%M:%SZ'

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

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
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class CrackingProScrapper(SiteMapScrapper):

    spider_class = CrackingProSpider
    site_name = 'crackingpro.com'
    site_type = 'forum'
