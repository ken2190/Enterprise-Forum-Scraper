import re
import uuid

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)
from datetime import datetime, timedelta


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class CardingSiteSpider(SitemapSpider):
    name = 'cardingsite_spider'

    # Url stuffs
    base_url = "https://cardingsite.cc/"

    # Xpath stuffs
    forum_xpath = '//div[@class="nodeText"]'\
                  '/h3[@class="nodeTitle"]/a/@href|'\
                  '//ol[@class="subForumList"]'\
                  '//h4[@class="nodeTitle"]/a/@href'

    pagination_xpath = '//a[@class="text" and text()="Next >"]/@href'

    thread_xpath = '//li[contains(@class,"discussionListItem ")]'
    thread_first_page_xpath = '//h3[@class="title"]/a[last()]/@href'
    thread_last_page_xpath = '//span[@class="itemPageNav"]/a[last()]/@href'
    thread_date_xpath = '//dl[@class="lastPostInfo"]//span[@class="DateTime"]'\
                        '/@title|//dl[@class="lastPostInfo"]'\
                        '//abbr[@class="DateTime"]/@data-datestring'
    thread_page_xpath = '//nav/a[contains(@class,"currentPage")]/text()'
    thread_pagination_xpath = '//nav/a[contains(text()," Prev")]/@href'

    post_date_xpath = '//div[@class="privateControls"]'\
                      '//span[@class="DateTime"]/text()|'\
                      '//div[@class="privateControls"]'\
                      '//abbr[@class="DateTime"]/@data-datestring'

    avatar_xpath = '//div[@class="avatarHolder"]/a/img/@src'

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
    sitemap_datetime_format = '%b %d, %Y'
    post_datetime_format = '%b %d, %Y'
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.split(' at')[0].strip()
        return datetime.strptime(
            thread_date.strip(),
            self.sitemap_datetime_format
        )

    def parse(self, response):

        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class CardingSiteSpider(SiteMapScrapper):

    spider_class = CardingSiteSpider
    site_name = 'cardingsite.cc'
