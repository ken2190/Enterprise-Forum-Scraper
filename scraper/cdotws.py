import time
import requests
import os
import json
import re
import scrapy
import uuid
from math import ceil
import configparser
from urllib.parse import urlencode
from lxml.html import fromstring
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from datetime import datetime, timedelta
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


USER = "Cyrax011"
PASS = "4hr63yh38a61SDW0"


class CdotWsSpider(SitemapSpider):
    name = 'cdotws_spider'
    base_url = 'https://cdotws.pw/'

    # Xpaths
    login_form_xpath = '//form[@method="post"]'
    forum_xpath = '//div[@class="datacontainer"]'\
                  '//h2[@class="forumtitle"]/a/@href|'\
                  '//li[@class="subforum"]/a/@href'
    thread_xpath = '//li[contains(@class, "threadbit ")]'
    thread_first_page_xpath = './/a[contains(@id,"thread_title_")]/@href'
    thread_last_page_xpath = './/dl[@class="pagination"]/dd'\
                             '/span[last()]/a/@href'
    thread_date_xpath = './/dl[@class="threadlastpost td"]'\
                        '//dd[last()]/text()[1]'
    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//span[@class="selected"]/a/text()'
    post_date_xpath = '//span[@class="date"]/text()[1]'

    avatar_xpath = '//a[contains(@href, "member.php?") and img/@src]'

    # Regex stuffs
    topic_pattern = re.compile(
        r't=(\d+)',
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r"u=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "On"
    sitemap_datetime_format = '%m-%d-%Y'
    post_datetime_format = '%m-%d-%Y'

    def get_topic_id(self, url=None):
        """
        :param url: str => thread url
        :return: str => extracted topic id from thread url
        """
        match = self.topic_pattern.findall(url)
        if not match:
            topic_pattern = re.compile(
                r'.*-(\d+)/',
                re.IGNORECASE
            )
            match = topic_pattern.findall(url)
        return match[0]

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.strip().strip(',')
        if 'today' in thread_date.lower():
            return datetime.today()
        elif 'yesterday' in thread_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        # Standardize thread_date
        post_date = post_date.strip().strip(',')
        if 'today' in post_date.lower():
            return datetime.today()
        elif 'yesterday' in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def parse(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)
        formdata = {
            'vb_login_username': USER,
            'vb_login_password': PASS,
            'cookieuser': '1'
        }
        yield FormRequest.from_response(
            response=response,
            formxpath=self.login_form_xpath,
            formdata=formdata,
            headers=self.headers,
            meta=self.synchronize_meta(response),
            callback=self.parse_redirect,
        )

    def parse_redirect(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response,
            meta=self.synchronize_meta(response),
            dont_filter=True,
            headers=self.headers,
            callback=self.parse_start,
        )

    def parse_start(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)
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
        yield from self.parse_avatars(response)

    def parse_avatars(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Save avatar content
        for avatar in response.xpath(self.avatar_xpath):
            avatar_url = avatar.xpath('img/@src').extract_first()

            # Standardize avatar url
            if not avatar_url.lower().startswith("http"):
                avatar_url = self.base_url + avatar_url

            if 'image/svg' in avatar_url:
                continue

            user_url = avatar.xpath('@href').extract_first()
            match = self.avatar_name_pattern.findall(user_url)
            if not match:
                continue

            file_name = os.path.join(
                self.avatar_path,
                f'{match[0]}.jpg'
            )

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
                ),
            )


class CdotWsScrapper(SiteMapScrapper):

    spider_class = CdotWsSpider
    site_name = 'cdotws.pw'
    site_type = 'forum'
