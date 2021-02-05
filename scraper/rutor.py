import re
from scrapy.http import Request
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'

PROXY = 'http://localhost:8118'


class RutorSpider(SitemapSpider):
    name = 'rutor_spider'
    base_url = 'http://rutordeepkpafpudl22pbbhzm4llbgncunvgcc66kax55sc4mp4kxcid.onion'

    # Xpaths
    forum_xpath = '//h3[@class="node-title"]/a/@href'
    thread_xpath = '//div[contains(@class, "structItem structItem--thread")]'
    thread_first_page_xpath = './/div[@class="structItem-title"]'\
                              '/a[contains(@href,"threads/")]/@href'
    thread_last_page_xpath = './/span[@class="structItem-pageJump"]'\
                             '/a[last()]/@href'
    thread_date_xpath = './/time[contains(@class, "structItem-latestDate")]'\
                        '/@datetime'
    pagination_xpath = '//a[contains(@class,"pageNav-jump--next")]/@href'
    thread_pagination_xpath = '//a[contains(@class, "pageNav-jump--prev")]'\
                              '/@href'
    thread_page_xpath = '//li[contains(@class, "pageNav-page--current")]'\
                        '/a/text()'
    post_date_xpath = '//div[@class="message-attribution-main"]'\
                      '/a/time/@datetime'

    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'

    # Other settings
    use_proxy = "Tor"
    sitemap_datetime_format = '%Y-%m-%dT%H:%M:%S'
    post_datetime_format = '%Y-%m-%dT%H:%M:%S'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    topic_pattern = re.compile(
        r".*threads/.*\.(\d+)/",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page-(\d+)",
        re.IGNORECASE
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update({
            "user-agent": USER_AGENT
        })

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                'proxy': PROXY
            },
            dont_filter=True
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

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
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class RutorScrapper(SiteMapScrapper):

    spider_class = RutorSpider
    site_name = 'rutor_rutorzzmfflzllk5'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings
