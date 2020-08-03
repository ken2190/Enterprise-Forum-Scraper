import os
import re

from scrapy.http import Request
from scrapy.exceptions import CloseSpider

from .base_scrapper import SitemapSpider, SiteMapScrapper


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class HackTheBoxSpider(SitemapSpider):
    name = 'hackthebox_scraper'
    base_url = 'https://forum.hackthebox.eu'

    # Xpaths
    forum_xpath = '//a[@class="Title"]/@href'

    thread_xpath = '//li[contains(@id, "Discussion_")]'
    thread_first_page_xpath = '//div[@class="Title"]/a/@href'
    thread_date_xpath = '//time/@title'

    thread_pagination_xpath = '//*[@id="PagerBefore"]/a[@rel="next"]/@href'
    thread_page_xpath = '//*[@id="PagerBefore"]/a[@aria-current]/text()'

    post_date_xpath = '//time/@title'

    avatar_xpath = '//*[contains(@class, "ProfilePhoto")]/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    topic_pattern = re.compile(
        r"discussion/(\d+)/",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = '%B %d, %Y %H:%S%p'
    post_datetime_format = '%B %d, %Y %H:%S%p'

    def start_requests(self):
        yield Request(
            url="https://forum.hackthebox.eu/categories",
            headers=self.headers
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def get_forum_next_page(self, response):
        pass

    def parse_thread(self, response):

        # Load all post date
        post_dates = [
            self.parse_post_date(post_date) for post_date in
            response.xpath(self.post_date_xpath).extract()
            if post_date.strip() and self.parse_post_date(post_date)
        ]
        if self.start_date and max(post_dates) < self.start_date:
            self.logger.info(
                "No more post to update."
            )

            # Thread pagination
            next_page = self.get_thread_next_page(response)
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
            return

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Get topic id
        topic_id = response.meta.get("topic_id")

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
                self.topic_pages_saved += 1

                # Update stats
                self.crawler.stats.set_value(
                    "topic pages saved",
                    self.topic_pages_saved
                )

                # Kill task if kill count met
                if self.kill and self.topic_pages_saved >= self.kill:
                    raise CloseSpider(reason="Kill count met, shut down.")

        # Thread pagination
        next_page = self.get_thread_next_page(response)
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

class HackTheBoxScrapper(SiteMapScrapper):
    spider_class = HackTheBoxSpider
