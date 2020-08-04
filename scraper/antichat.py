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


USER = 'blacklotus2000@protonmail.com'
PASS = 'Night#Anti999'
REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class AntichatSpider(SitemapSpider):
    name = 'antichat_spider'

    # Url stuffs
    base_url = "https://forum.antichat.ru/"

    # Xpath stuffs
    forum_xpath = '//div[@class="nodelistBlock nodeText"]'\
                  '/h3[@class="nodeTitle"]/a/@href|'\
                  '//ol[@class="subForumList"]'\
                  '//h4[@class="nodeTitle"]/a/@href'

    pagination_xpath = '//a[@class="text" and text()="Next >"]/@href'

    thread_xpath = '//li[contains(@class,"discussionListItem ")]'
    thread_first_page_xpath = '//h3[@class="title"]/a/@href'
    thread_last_page_xpath = '//span[@class="itemPageNav"]/a[last()]/@href'
    thread_date_xpath = '//dl[@class="lastPostInfo"]//span[@class="DateTime"]'\
                        '/@title|//dl[@class="lastPostInfo"]'\
                        '//abbr[@class="DateTime"]/text()'
    thread_page_xpath = '//nav/a[contains(@class,"currentPage")]/text()'
    thread_pagination_xpath = '//nav/a[contains(text()," Prev")]/@href'

    post_date_xpath = '//div[@class="messageDetails"]'\
                      '//span[@class="DateTime"]/@title|'\
                      '//div[@class="messageDetails"]'\
                      '//abbr[@class="DateTime"]/text()'

    avatar_xpath = '//a[@data-avatarhtml="true"]/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"/threads/(\d+)/",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\w+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r"page-(\d+)",
        re.IGNORECASE
    )

    # Other settings
    sitemap_datetime_format = '%d %b %Y at %H:%M %p'
    post_datetime_format = '%d %b %Y at %H:%M %p'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "Sec-fetch-mode": "navigate",
                "Sec-fetch-site": "same-origin",
                "Sec-fetch-user": "?1",
            }
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
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "cookiejar": uuid.uuid1().hex
                    }
                )
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class AntichatScrapper(SiteMapScrapper):

    spider_class = AntichatSpider
    site_name = 'antichat.ru'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
            }
        )
        return settings
