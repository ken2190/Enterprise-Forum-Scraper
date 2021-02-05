import os
import re

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)
from scrapy import Request, Selector

from datetime import datetime
import dateparser
import requests
import lxml.html

class NulledBBSpider(SitemapSpider):

    name = 'nulledbb_spider'

    # Url stuffs
    base_url = "https://nulledbb.com/"
    start_urls = ["https://nulledbb.com/"]

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r'.*avatar_(\d+\.\w+)',
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r'.*page=(\d+)',
        re.IGNORECASE
    )


    # Xpath stuffs
    forum_xpath = '//section[contains(@class, "subforums")]//li[contains(@class, "mb-1")]/a/@href |'\
            '//section[contains(@class, "forumdisplay-subforum")]//div[contains(@class, "forum-title")]/a/@href'

    thread_xpath = '//article[contains(@class, "thread")]'
    pagination_xpath = '//a[@class="pagination_next"]/@href'
    thread_first_page_xpath = './/span[contains(@id, "tid_")]'\
                              '/a[contains(@href, "thread-")]/@href'
    thread_last_page_xpath = './/a[contains(@href, "action=newpost")]/@href'
    # thread_date_xpath = './/div[contains(@class,"threadlist-lastpost")]/span/*[last()]/span/@title|'\
    #                     './/div[contains(@class,"threadlist-lastpost")]/span/*[last()]/text()'

    avatar_xpath = '//a[contains(@class, "post-avatar")]/img/@src'

    thread_page_xpath = '//a[contains(@class,"pagination_current")]/text()'

    thread_pagination_xpath = '//a[contains(@class, "pagination_previous")]/@href'

    post_date_xpath = '//span[@data-toggle]/text()'
    
    use_proxy="On"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "Referer": "https://nulledbb.com/",
                "Sec-fetch-mode": "navigate",
                "Sec-fetch-site": "none",
                "Sec-fetch-user": "?1"
            }
        )

    def extract_thread_stats(self, thread):
        """
        :param thread: str => thread html contain url and last mod
        :return: thread url: str, thread lastmod: datetime
        """
        # Load selector
        # selector = Selector(text=thread)

        # Load stats
        thread_first_page_url = None
        if self.thread_first_page_xpath:
            thread_first_page_url = thread.xpath(
                self.thread_first_page_xpath
            ).extract_first()

        thread_last_page_url = None
        if self.thread_last_page_xpath:
            thread_last_page_url = thread.xpath(
                self.thread_last_page_xpath
            ).extract_first()

        # Process stats
        try:
            thread_url = (self.parse_thread_url(thread_last_page_url)
                          or self.parse_thread_url(thread_first_page_url))
        except Exception as err:
            thread_url = None

        return thread_url
    
    def parse_forum(self, response, thread_meta={}, is_first_page=True):

        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        self.logger.info(
            "Next_page_url: %s" % response.url
        )

        threads = response.xpath(self.thread_xpath)

        lastmod_pool = []
        for thread in threads:
            thread_url = self.extract_thread_stats(thread)
            thread_lastmod = None

            # Standardize thread url only if it is not complete url
            if 'http://' not in thread_url and 'https://' not in thread_url:
                temp_url = thread_url
                if self.base_url not in thread_url:
                    temp_url = response.urljoin(thread_url)

                if self.base_url not in temp_url:
                    temp_url = self.base_url + thread_url

                # last_page = requests.get(temp_url)
                # last_page = lxml.html.fromstring(last_page.text)
                # thread_lastmod = last_page.xpath(self.post_date_xpath)[-1].strip()

            if not thread_url:
                self.crawler.stats.inc_value("mainlist/detail_no_url_count")
                self.logger.warning(
                    "Unable to find thread URL on the forum: %s",
                    response.url
                )
                continue

            # Parse topic id
            topic_id = self.get_topic_id(thread_url)
            if not topic_id:
                self.crawler.stats.inc_value("mainlist/detail_no_topic_id_count")
                self.logger.warning(
                    "Unable to find topic ID of the thread: %s",
                    response.urljoin(thread_url)
                )
                continue

            if thread_lastmod is None:
                if topic_id not in self.topics:
                    self.topics.add(topic_id)
                    self.crawler.stats.inc_value("mainlist/detail_no_date_count")
                    self.crawler.stats.set_value("mainlist/detail_count", len(self.topics))

                if self.start_date:
                    self.logger.info(
                        "Date not found in thread %s " % thread_url
                    )
                    continue
            else:
                lastmod_pool.append(thread_lastmod)

            # If start date, check last mod
            if self.start_date and thread_lastmod < self.start_date:
                if topic_id not in self.topics:
                    self.topics.add(topic_id)
                    self.crawler.stats.inc_value("mainlist/detail_outdated_count")
                    self.crawler.stats.set_value("mainlist/detail_count", len(self.topics))

                self.logger.info(
                    "Thread %s last updated is %s before start date %s. Ignored." % (
                        thread_url, thread_lastmod, self.start_date
                    )
                )
                continue

            # Standardize thread url only if it is not complete url
            if 'http://' not in thread_url and 'https://' not in thread_url:
                temp_url = thread_url
                if self.base_url not in thread_url:
                    temp_url = response.urljoin(thread_url)

                if self.base_url not in temp_url:
                    temp_url = self.base_url + thread_url

                thread_url = temp_url

            # Check file exist
            if self.check_existing_file_date(
                    topic_id=topic_id,
                    thread_date=thread_lastmod,
                    thread_url=thread_url
            ):
                # update stats
                if topic_id not in self.topics:
                    self.topics.add(topic_id)
                    self.crawler.stats.inc_value("mainlist/detail_already_scraped_count")
                    self.crawler.stats.set_value("mainlist/detail_count", len(self.topics))

                continue

            # Check thread meta
            if thread_meta:
                meta = thread_meta
            else:
                meta = self.synchronize_meta(response)

            # Update topic id
            meta["topic_id"] = topic_id

            # update stats
            self.topics.add(topic_id)
            self.crawler.stats.set_value("mainlist/detail_count", len(self.topics))

            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta=meta
            )

        # get next page
        next_page = self.get_forum_next_page(response)
        if is_first_page and next_page:
            self.crawler.stats.inc_value("mainlist/mainlist_next_page_count")

        # Pagination
        if not lastmod_pool:
            self.crawler.stats.inc_value("mainlist/mainlist_no_detail_count")
            self.logger.info(
                "Forum without thread, exit: %s",
                response.url
            )
            return

        # update stats
        if is_first_page:
            self.crawler.stats.inc_value("mainlist/mainlist_processed_count")

        if self.start_date and self.start_date > max(lastmod_pool):
            self.logger.info(
                "Found no more thread update later than %s in forum %s. Exit." % (
                    self.start_date,
                    response.url
                )
            )
            return

        if next_page:
            yield Request(
                url=next_page,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
                cb_kwargs={'is_first_page': False}
            )

    def parse_thread_date(self, post_date):
        try:
            date = post_date.split('Posted: ')[-1]
            return dateparser.parse(date).replace(tzinfo=None)
        except:
            return datetime.now()

    def parse_post_date(self, post_date):
        try:
            date = post_date.split('Posted: ')[-1]
            return dateparser.parse(date).replace(tzinfo=None)
        except:
            return datetime.now()

    def parse_thread(self, response):
        yield from super().parse_thread(response)
        yield from super().parse_avatars(response)

class NulledBBScrapper(SiteMapScrapper):

    spider_class = NulledBBSpider
    site_name = 'nulledbb.com'
    site_type = 'forum'

