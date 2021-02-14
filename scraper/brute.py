import re
import uuid
from scrapy.http import Request
import dateparser
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


class BruteSpider(SitemapSpider):
    name = 'brute_spider'
    base_url = 'https://brute.pw'

    # Xpaths
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
    post_date_xpath = '//div[@class="message-attribution-main"]'\
                      '//time[@datetime]/@datetime'

    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"/threads/(\d+)",
        re.IGNORECASE
    )

    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    pagination_pattern = re.compile(
        r".*/page-(\d+)",
        re.IGNORECASE
    )

    #captcha stuffs
    ip_check_xpath = "//text()[contains(.,\"Your IP\")]"
    check_solved_xpath = '//h3[@class="node-title"]'

    # Recaptcha stuffs
    recaptcha_site_key_xpath = '//div[@data-xf-init="re-captcha"]/@data-sitekey'

    # Other settings
    use_proxy = "On"
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    def start_requests(self):
        # Temporary action to start spider
        yield Request(
            url=self.temp_url,
            headers=self.headers,
            callback=self.pass_cloudflare
        )

    def pass_cloudflare(self, response):
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
                base_url=self.base_url,
                proxy=True,
                fraud_check=True
            )

        yield from self.start_requests(cookies=cookies, ip=ip)

    def check_bypass_success(self, browser):
        if ("blocking your access based on IP address" in browser.page_source or
                browser.find_elements_by_css_selector('.cf-error-details')):
            raise RuntimeError("HackForums.net is blocking your access based on IP address.")

        element = browser.find_elements_by_xpath(self.check_solved_xpath)
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
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):

        # Parse generic thread
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


class BruteScrapper(SiteMapScrapper):

    spider_class = BruteSpider
    site_name = 'brute.su'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings
