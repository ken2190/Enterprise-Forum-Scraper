import re
import uuid
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper
from scrapy import Request

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'
REQUEST_DELAY = 1
NO_OF_THREADS = 4


class BlackHatWorldSpider(SitemapSpider):
    name = 'blackhatworld_spider'

    base_url = "https://www.blackhatworld.com/"
    start_url = 'https://www.blackhatworld.com/forums/'

    forum_xpath = '//h3[@class="node-title"]/a/@href|'\
                  '//a[contains(@class,"subNodeLink--forum")]/@href'
    thread_xpath = '//div[contains(@class, "structItem structItem--thread")]'
    thread_first_page_xpath = './/div[@class="structItem-title"]/a/@href'
    thread_last_page_xpath = './/span[@class="structItem-pageJump"]'\
                             '/a[last()]/@href'
    thread_date_xpath = './/time[contains(@class, "structItem-latestDate")]'\
                        '/@datetime'
    pagination_xpath = '//a[contains(@class,"pageNav-jump--next")]/@href'
    thread_pagination_xpath = '//a[contains(@class, "pageNav-jump--prev")]'\
                              '/@href'
    thread_page_xpath = '//li[contains(@class, "pageNav-page--current")]'\
                        '/a/text()'
    post_date_xpath = '//div/a/time[@datetime]/@datetime'

    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'

    # Other settings
    use_proxy = True
    handle_httpstatus_list = [403]
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    # Regex stuffs
    topic_pattern = re.compile(
        r".*\.(\d+)/",
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

    username_pattern = re.compile(
        r'members/(.*)\.\d+',
        re.IGNORECASE
    )

    def start_requests(self):
        yield Request(self.start_url, self.parse)

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


class BlackHatWorldScrapper(SiteMapScrapper):

    spider_class = BlackHatWorldSpider
    site_name = 'blackhatworld.com'

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
