import os
import re

from scrapy import Request

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


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
    forum_xpath = '//section[contains(@class, "subforums")]//li[contains(@class, "mb-1")]/a/@href |' \
                  '//section[contains(@class, "forumdisplay-subforum")]' \
                  '//div[contains(@class, "forum-title")]/a/@href'

    thread_xpath = '//article[contains(@class, "thread")]'
    pagination_xpath = '//a[contains(@class, "pagination_next")]/@href'
    thread_first_page_xpath = './/span[contains(@id, "tid_")]' \
                              '/a[contains(@href, "thread-")]/@href'
    last_page_xpath = '//div[contains(@class, "pagination")]//ul/li[last()]/a/@href'

    avatar_xpath = '//a[contains(@class, "post-avatar")]/img/@src'

    thread_page_xpath = '//a[contains(@class,"pagination_current")]/text()'

    thread_pagination_xpath = '//a[contains(@class, "pagination_previous")]/@href'

    post_date_xpath = '//div[@class="flex-fill"]/span[@data-toggle="tooltip"]/text()'

    use_proxy = "On"

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

        # Parse sub forums
        yield from self.parse(response)

        threads = response.xpath(self.thread_xpath)

        for thread in threads:
            thread_url = self.extract_thread_stats(thread)

            topic_id = self.get_topic_id(thread_url)

            # Standardize thread url only if it is not complete url
            if 'http://' not in thread_url and 'https://' not in thread_url:
                temp_url = thread_url
                if self.base_url not in thread_url:
                    temp_url = response.urljoin(thread_url)

                if self.base_url not in temp_url:
                    temp_url = self.base_url + thread_url

                thread_url = temp_url

            if thread_meta:
                meta = thread_meta
            else:
                meta = self.synchronize_meta(response)
            meta["topic_id"] = str(topic_id)

            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.process_forum,
                meta=meta
            )

        # get next page
        next_page = self.get_forum_next_page(response)
        if next_page:
            yield Request(
                url=next_page,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
                cb_kwargs={'is_first_page': False}
            )

    def process_forum(self, response):
        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Get topic id
        topic_id = response.meta.get("topic_id")

        thread_last_page_url = response.xpath(
            self.last_page_xpath
        ).extract_first()

        if thread_last_page_url:
            thread_last_page_url = self.parse_thread_url(thread_last_page_url)

            # Standardize thread url only if it is not complete url
            if 'http://' not in thread_last_page_url and 'https://' not in thread_last_page_url:
                temp_url = thread_last_page_url
                if self.base_url not in thread_last_page_url:
                    temp_url = response.urljoin(thread_last_page_url)

                if self.base_url not in temp_url:
                    temp_url = self.base_url + thread_last_page_url

                thread_last_page_url = temp_url
        else:
            thread_last_page_url = response.url

        yield Request(
            url=thread_last_page_url,
            headers=self.headers,
            callback=self.parse_thread,
            meta=self.synchronize_meta(
                response,
                default_meta={
                    "topic_id": topic_id
                }
            )
        )

    def parse_thread(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Get topic id
        topic_id = response.meta.get("topic_id")

        # Load all post date
        post_dates = [
            self.parse_post_date(post_date) for post_date in
            response.xpath(self.post_date_xpath).extract()
            if post_date.strip() and self.parse_post_date(post_date)
        ]

        if self.start_date and not post_dates:
            self.logger.info('No dates found in thread: %s', response.url)
            return

        # get next page
        next_page = self.get_thread_next_page(response)
        if next_page:
            self.crawler.stats.inc_value("mainlist/detail_next_page_count")

        # check if the thread contains new messages
        if self.start_date and max(post_dates) < self.start_date:
            if topic_id not in self.topics_scraped:
                self.crawler.stats.inc_value("mainlist/detail_outdated_count")

            self.logger.info(
                "No more post to update."
            )
            return

        # Save thread content
        if not self.useronly:
            current_page = self.get_thread_current_page(response)
            with open(
                    file=os.path.join(
                        self.output_path,
                        "%s-%s.html" % (
                                topic_id,
                                current_page
                        )
                    ),
                    mode="w+",
                    encoding="utf-8"
            ) as file:
                file.write(response.text)
            self.logger.info(
                f'{topic_id}-{current_page} done..!'
            )

            # Update stats
            self.topics_scraped.add(topic_id)
            self.crawler.stats.set_value(
                "mainlist/detail_saved_count",
                len(self.topics_scraped)
            )

        # Thread pagination
        if next_page:
            yield Request(
                url=next_page,
                headers=self.headers,
                callback=self.parse_thread,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "topic_id": topic_id
                    }
                )
            )

        yield from super().parse_avatars(response)


class NulledBBScrapper(SiteMapScrapper):
    spider_class = NulledBBSpider
    site_name = 'nulledbb.com'
    site_type = 'forum'
