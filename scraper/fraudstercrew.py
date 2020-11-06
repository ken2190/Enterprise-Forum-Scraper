import re
from scrapy import (
    Request
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

USER = 'Cyrax_011'
PASS = 'Night#India065'

REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class FraudstercrewSpider(SitemapSpider):
    name = 'fraudstercrew_spider'
    # Url stuffs
    # base_url = "https://fraudstercrew.su"
    base_url = "https://fssquad.com/"
    start_urls = [base_url]
    # Regex stuffs
    topic_pattern = re.compile(
        r'threads/.*\.(\d+)/',
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page-(\d+)",
        re.IGNORECASE
    )

    # xpath stuffs
    forum_xpath = '//h3[@class="node-title"]/a/@href|'\
                  '//a[contains(@class,"subNodeLink--forum")]/@href'
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
    post_date_xpath = '//a[contains(@href, "/threads/")]/time[@datetime]'\
                      '/@datetime'

    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'

    # Other settings
    use_proxy = True

    def parse_thread(self, response):
        yield from super().parse_thread(response)
        yield from super().parse_avatars(response)

class FraudstercrewScrapper(SiteMapScrapper):

    spider_class = FraudstercrewSpider
    site_name = 'fraudstercrew.su'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
                'RETRY_HTTP_CODES': [403, 429, 500, 503, 504],
            }
        )
        return settings
