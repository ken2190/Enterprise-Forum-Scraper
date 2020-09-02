import re
import uuid
from urllib.parse import urlencode
import dateparser
from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

REQUEST_DELAY = 0.3
NO_OF_THREADS = 5

USER = "Cyrax011"
PASS = "4hr63yh38a61SDW0"


class XakerSpider(SitemapSpider):
    name = 'xaker_spider'

    # Url stuffs
    base_url = "http://xaker.name/"

    # Xpath stuffs
    forum_xpath = '//ol[@class="nodeList"]//h3/a/@href'
    thread_xpath = '//ol[@class="discussionListItems"]/li'
    thread_first_page_xpath = '//h3[@class="title"]'\
                              '/a[contains(@href,"threads/")]/@href'
    thread_last_page_xpath = '//span[@class="itemPageNav"]'\
                             '/a[last()]/@href'

    thread_date_xpath = '//dl[@class="lastPostInfo"]//a[@class'\
                        '="dateTime"]/abbr/@data-datestring|//'\
                        'dl[@class="lastPostInfo"]//a[@class="dateTime"]/span/@title'

    pagination_xpath = '//nav/a[last()]/@href'
    thread_pagination_xpath = '//nav/a[@class="text"]/@href'
    thread_page_xpath = '//nav//a[contains(@class, "currentPage")]'\
                        '/text()'
    post_date_xpath = '//div[@class="messageDetails"]'\
                      '//span[@class="DateTime"]/text()|'\
                      '//div[@class="messageDetails"]'\
                      '//abbr[@class="DateTime"]/@data-datestring'

    avatar_xpath = '//div[contains(@class,"avatarHolder")]//img/@src'

    #captcha stuffs
    ip_check_xpath = "//text()[contains(.,\"Your IP\")]"

    # Regex stuffs
    topic_pattern = re.compile(
        r"threads/(\d+).*",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\d+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*/page-(\d+)",
        re.IGNORECASE
    )

    # Recaptcha stuffs
    recaptcha_site_key_xpath = '//div[@data-xf-init="re-captcha"]/@data-sitekey'

    # Other settings
    use_proxy = True
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS


    def start_requests(self, cookies=None, ip=None):
        # Load cookies and ip
        cookies, ip = self.get_cloudflare_cookies(
            base_url=self.base_url,
            proxy=True,
            fraud_check=True
        )


        # Init request kwargs and meta
        meta = {
            "cookiejar": uuid.uuid1().hex,
            "ip": ip
        }

        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta=meta,
            cookies=cookies,
            callback=self.parse_start
        )

    def parse_captcha(self, response):
        ip_ban_check = response.xpath(
            self.ip_check_xpath
        ).extract_first()

        # Init cookies, ip
        cookies, ip = None, None

        # Report bugs
        if "error code: 1005" in response.text:
            self.logger.info(
                "Ip for error 1005 code. Rotating."
            )
        elif ip_ban_check:
            self.logger.info(
                "%s has been permanently banned. Rotating." % ip_ban_check
            )
        else:
            cookies, ip = self.get_cloudflare_cookies(
                base_url=self.login_url,
                proxy=True,
                fraud_check=True
            )

        yield from self.start_requests(cookies=cookies, ip=ip)


    def check_bypass_success(self, browser):
        if ("blocking your access based on IP address" in browser.page_source or
                browser.find_elements_by_css_selector('.cf-error-details')):
            raise RuntimeError("HackForums.net is blocking your access based on IP address.")

        element = browser.find_elements_by_xpath('//ol[@class="nodeList"]//h3/a')
        return bool(element)

    def parse_start(self, response):

        # Synchronize user agent for cloudfare middlewares
        self.synchronize_headers(response)

        # If captcha detected
        if response.status in [503, 403]:
            yield from self.parse_captcha(response)
            return
            

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        for forum_url in all_forums:
            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url

            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )


    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.strip()[:-5]
        if not thread_date:
            return
        return dateparser.parse(thread_date)

    def parse_post_date(self, post_date):
        post_date = post_date.strip()[:-5]
        return dateparser.parse(post_date)


class XakerScrapper(SiteMapScrapper):

    spider_class = XakerSpider
    site_name = 'xaker.name'

    def load_settings(self):
        spider_settings = super().load_settings()
        return spider_settings
