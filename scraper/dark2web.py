import re
from datetime import datetime

from scrapy.http import Request, FormRequest

from scraper.base_scrapper import SitemapSpider, SiteMapScrapper

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36'
MIN_DELAY = 1
MAX_DELAY = 3

USER = 'gordal418'
PASS = 'Nightlion#123'


class Dark2WebSpider(SitemapSpider):
    name = 'dark2web_spider'
    base_url = 'https://dark2web.net'
    login_url = 'https://dark2web.net/login/login'

    # Xpaths
    forum_xpath = '//h3[@class="node-title"]/a/@href|' \
                  '//a[contains(@class,"subNodeLink--forum")]/@href'
    thread_xpath = '//div[contains(@class, "structItem structItem--thread")]'
    thread_first_page_xpath = './/div[@class="structItem-title"]' \
                              '/a[contains(@href,"threads/")]/@href'
    thread_last_page_xpath = './/span[@class="structItem-pageJump"]' \
                             '/a[last()]/@href'
    thread_date_xpath = './/time[contains(@class, "structItem-latestDate")]' \
                        '/@data-time'
    pagination_xpath = '//a[contains(@class,"pageNav-jump--next")]/@href'
    thread_pagination_xpath = '//a[contains(@class, "pageNav-jump--prev")]' \
                              '/@href'
    thread_page_xpath = '//li[contains(@class, "pageNav-page--current")]' \
                        '/a/text()'
    post_date_xpath = '//ul[contains(@class, "message-attribution-main")]' \
                      '//time[@data-time]/@data-time'

    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'

    # Recaptcha stuffs
    recaptcha_site_key_xpath = '//div[@data-xf-init="re-captcha"]/@data-sitekey'

    use_proxy = 'VIP'
    # Regex stuffs
    topic_pattern = re.compile(
        r"/threads/(\d+)",
        re.IGNORECASE
    )

    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    # Other settings
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept-Encoding": "gzip, deflate"
            }
        )

    def start_requests(self):
        yield Request(
            url=self.login_url,
            headers=self.headers,
            callback=self.proceed_for_login
        )

    def proceed_for_login(self, response):
        self.synchronize_headers(response)

        # Extract csrf token
        token = response.xpath(
            '//input[@name="_xfToken"]/@value').extract_first()
        params = {
            'login': USER,
            'password': PASS,
            "remember": '1',
            '_xfRedirect': '/',
            '_xfToken': token,
        }

        yield FormRequest(
            url=self.login_url,
            callback=self.parse,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
            meta=self.synchronize_meta(response),
        )

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        try:
            return datetime.fromtimestamp(float(thread_date))
        except:
            return datetime.strptime(
                thread_date.strip(),
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        try:
            return datetime.fromtimestamp(float(post_date))
        except:
            return datetime.strptime(
                post_date.strip(),
                self.post_datetime_format
            )

    def parse_thread(self, response):
        # Parse generic thread
        yield from super().parse_thread(response)
        # Save avatars
        yield from super().parse_avatars(response)


class Dark2WebScrapper(SiteMapScrapper):
    spider_class = Dark2WebSpider
    site_name = 'dark2web.ru'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [403, 406, 429, 500, 503],
                "AUTOTHROTTLE_ENABLED": True,
                "AUTOTHROTTLE_START_DELAY": MIN_DELAY,
                "AUTOTHROTTLE_MAX_DELAY": MAX_DELAY
            }
        )
        return settings
