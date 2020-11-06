import re
from scrapy.http import Request, FormRequest
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


REQUEST_DELAY = 0.2
NO_OF_THREADS = 10

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6)'\
             ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'\
             '76.0.3809.132 Safari/537.36'

USER = 'blackbay'
PASS = 'Night#Marv'


class MarviherSpider(SitemapSpider):
    name = 'marviher_spider'
    # xpaths
    forum_xpath = '//div[@class="ipsDataItem_main"]//h4/a/@href'

    pagination_xpath = '//li[@class="ipsPagination_next"]/a/@href'

    thread_xpath = '//ol/li[contains(@class,"ipsDataItem")]'
    thread_first_page_xpath = './/span[@class="ipsType_break ipsContained"]'\
                              '/a/@href'
    thread_last_page_xpath = './/span[@class="ipsPagination_page"][last()]'\
                             '/a/@href'

    thread_date_xpath = '//li[@class="ipsType_light"]/a/time/@datetime'
    thread_page_xpath = '//li[contains(@class, "ipsPagination_active")]'\
                        '/a/text()'
    thread_pagination_xpath = '//li[@class="ipsPagination_prev"]'\
                              '/a/@href'

    post_date_xpath = '//a/time[@datetime]/@datetime'

    avatar_xpath = '//li[@class="cAuthorPane_photo"]/a/img/@src'

    # Other settings
    use_proxy = True
    sitemap_datetime_format = '%Y-%m-%dT%H:%M:%SZ'
    post_datetime_format = '%Y-%m-%dT%H:%M:%SZ'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://marviher.club/"
        self.topic_pattern = re.compile(r'topic/(\d+)-')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*/page/(\d+)/')
        self.start_url = 'https://marviher.club/'
        self.headers = {
            "user-agent": USER_AGENT
        }

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        login_url = 'https://marviher.club/login/'
        csrf = response.xpath(
            '//input[@name="csrfKey"]/@value').extract_first()
        formdata = {
            'csrfKey': csrf,
            'auth': USER,
            'password': PASS,
            'remember_me': '1',
            '_processLogin': 'usernamepassword',
            '_processLogin': 'usernamepassword',
        }
        yield FormRequest(
            url=login_url,
            formdata=formdata,
            headers=self.headers,
            meta=self.synchronize_meta(response),
            callback=self.parse_main_page,
            dont_filter=True,
        )

    def parse_main_page(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = response.urljoin(forum_url)

            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class MarviherScrapper(SiteMapScrapper):

    spider_class = MarviherSpider
    site_name = 'marviher.club'
    site_type = 'forum'

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
