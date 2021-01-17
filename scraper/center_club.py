import re
import uuid

from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


USER = 'vrx9'
PASS = 'Night#Pro000'


class CenterClubSpider(SitemapSpider):
    name = 'centerclub_spider'

    # Url stuffs
    base_url = "https://center-club.us"
    index_url = "https://center-club.us/index.php"

    # Xpaths
    login_form_xpath = '//form[@method="post"]'
    # captcha_form_xpath = '//form[@id="recaptcha-form"]'
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
    post_date_xpath = '//div/a/time[@datetime]/@datetime'

    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'

    # Recaptcha stuffs
    recaptcha_site_key_xpath = '//button[@class="g-recaptcha"]/@data-sitekey'
    bypass_success_xpath = '//h3[@class="node-title"]'

    # Other settings
    use_proxy = "On"
    handle_httpstatus_list = [403]
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    # Regex stuffs
    topic_pattern = re.compile(
        r'threads/.*\.(\d+)/',
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    def start_requests(self, cookies=None, ip=None):
        meta = {
            "cookiejar": uuid.uuid1().hex,
        }

        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta=meta,
            callback=self.parse
        )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class CenterClubScrapper(SiteMapScrapper):

    spider_class = CenterClubSpider
    site_name = 'center-club.us'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update({
            'RETRY_HTTP_CODES': [403, 406, 429, 500, 503]
        })
        return settings
