import re
from scrapy.http import Request
import locale
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


REQUEST_DELAY = 0.2
NO_OF_THREADS = 10

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0)'\
             ' Gecko/20100101 Firefox/68.0'

PROXY = 'http://127.0.0.1:8118'


class Galaxy3Spider(SitemapSpider):
    name = 'galaxy3_spider'
    start_url = 'http://galaxy3m2mn5iqtn.onion/thewire/all'
    base_url = 'http://galaxy3m2mn5iqtn.onion'

    # Xpaths
    pagination_xpath = '//li/a[contains(text(), "Next")]/@href'
    thread_xpath = '//ul[contains(@class, "elgg-list")]/li'
    thread_first_page_xpath = './/a[contains(text(), "Thread") and '\
                              'contains(@href, "thewire/thread/")]/@href'
    thread_date_xpath = './/div/time[@datetime]/@datetime'
    thread_pagination_xpath = '//li/a[contains(text(), "Next")]/@href'
    thread_page_xpath = '//li[@class="elgg-state-selected"]/span/text()'
    post_date_xpath = '//div/time[@datetime]/@datetime'

    avatar_xpath = '//div[contains(@class,"elgg-avatar")]/a/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"onion/(\w+)/.*",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = False
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.headers.update({
            "user-agent": USER_AGENT
        })

    def start_requests(self):
        yield Request(
            url=self.start_url,
            callback=self.parse,
            headers=self.headers,
            meta={
                'proxy': PROXY
            },
            dont_filter=True
        )

    def parse(self, response):
        topic_id = self.get_topic_id(response.url)
        response.meta.update({'topic_id': topic_id})
        yield from self.parse_thread(response)

    def get_topic_id(self, url=None):
        """
        :param url: str => thread url
        :return: str => extracted topic id from thread url
        """
        topic_id = self.topic_pattern.findall(url)[0]

        topic_id = str(
            int.from_bytes(
                url.encode('utf-8'),
                byteorder='big'
            ) % (10 ** 7)
        )

        return topic_id

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class Galaxy3Scrapper(SiteMapScrapper):

    spider_class = Galaxy3Spider
    site_name = 'galaxy3_lgalaxy3m2mn5iqtn'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings
