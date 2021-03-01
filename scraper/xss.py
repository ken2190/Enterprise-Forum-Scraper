import re
import uuid

from scrapy import Request, FormRequest
from scrapy.exceptions import CloseSpider

from scraper.base_scrapper import SitemapSpider, SiteMapScrapper

LOGINS = [
    {"USER":"GalactusPrime", "PASS":"KXpro218gj2"},
    {"USER":"USER1", "PASS":"PASS1"},
    {"USER":"USER2", "PASS":"PASS2"},
    {"USER":"USER3", "PASS":"PASS3"},
]

MIN_DELAY = 1
MAX_DELAY = 3

class XSSSpider(SitemapSpider):
    name = "xss_spider"

    # Url stuffs
    base_url = "https://xss.is"
    login_url = "https://xss.is/login/login"

    # Selectors
    login_form_xpath = "//form[@action='/login/login']"
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
    post_date_xpath = '//div[contains(@class, "message-cell--main")]//a/time[@datetime]/@datetime'
    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'

    # captcha success
    bypass_success_xpath = '//div[contains(@class,"xb")]'

    # regexps
    topic_pattern = re.compile(r"threads/(\d+)/", re.IGNORECASE)
    avatar_name_pattern = re.compile(r".*/(\S+\.\w+)", re.IGNORECASE)
    pagination_pattern = re.compile(r".*page-(\d+)$", re.IGNORECASE)

    # Other settings
    use_proxy = "VIP"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    # Login Failed Message
    login_failed_xpath = '//div[contains(@class, "blockMessage")]'

    def start_requests(self):

        yield Request(
            url=self.login_url,
            headers=self.headers,
            callback=self.parse_start
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        login = self.get_login(LOGINS)
        print(login)
        yield FormRequest.from_response(
            response,
            formxpath=self.login_form_xpath,
            formdata={
                "login": login["USER"],
                "password": login["PASS"]
            },
            headers=self.headers,
            meta=self.synchronize_meta(response),
            dont_filter=True,
            callback=self.check_if_logged_in
        )

    def check_if_logged_in(self, response):
        # check if logged in successfully
        if response.xpath(self.forum_xpath):
            # start forum scraping
            yield from self.parse(response)
            return

        super().check_if_logged_in(response)

        err_msg = response.css('div.blockMessage--error::text').get() or 'Unknown error'
        self.logger.error('Unable to log in: %s', err_msg)

    def parse_thread(self, response):
        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class XSSScrapper(SiteMapScrapper):

    spider_class = XSSSpider
    site_name = 'xss.is'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'HTTPERROR_ALLOWED_CODES': [403],
                "AUTOTHROTTLE_ENABLED": True,
                "AUTOTHROTTLE_START_DELAY": MIN_DELAY,
                "AUTOTHROTTLE_MAX_DELAY": MAX_DELAY
            }
        )
        return settings
