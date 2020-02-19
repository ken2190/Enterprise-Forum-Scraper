import os
import re
import time
import uuid
import json

from datetime import datetime
from scrapy.utils.gz import gunzip

from seleniumwire.webdriver import (
    Chrome,
    ChromeOptions
)
from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper,
    PROXY_USERNAME,
    PROXY_PASSWORD,
    PROXY
)


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class CardingTeamSpider(SitemapSpider):
    name = 'cardingteam_spider'

    # Url stuffs
    base_url = "https://cardingteam.cc/"
    sitemap_url = 'https://cardingteam.cc/sitemap-index.xml'
    ip_url = "https://api.ipify.org?format=json"

    # Sitemap Stuffs
    forum_sitemap_xpath = '//sitemap[loc[contains(text(),"sitemap-threads.xml")] and lastmod]/loc/text()'
    thread_sitemap_xpath = '//url[loc[contains(text(),"Thread-")] and lastmod]'
    thread_url_xpath = '//loc/text()'
    thread_lastmod_xpath = "//lastmod/text()"

    # Css stuffs
    ip_css = "pre::text"

    # Xpath stuffs
    forum_xpath = '//a[contains(@href, "Forum-")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[@class="pagination_next"]/@href'
    thread_xpath = '//tr[@class="inline_row"]'
    thread_first_page_xpath = '//span[contains(@id,"tid_")]/a/@href'
    thread_last_page_xpath = '//td[contains(@class,"forumdisplay_")]/div'\
                             '/span/span[contains(@class,"smalltext")]'\
                             '/a[last()]/@href'
    thread_date_xpath = '//td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/text()[1]|'\
                        '//td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/span/@title'
    thread_pagination_xpath = '//div[@class="pagination"]'\
                              '//a[@class="pagination_previous"]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//span[@class="post_date2"]/text()[1]|'\
                      '//span[@class="post_date2"]/span/@title'\

    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )

    def get_cookies(self, proxy=None):
        # Init options
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument(f'user-agent={self.headers.get("User-Agent")}')

        # Init web driver arguments
        webdriver_kwargs = {
            "executable_path": "/usr/local/bin/chromedriver",
            "options": options
        }

        # Init proxy
        if proxy:
            proxy_options = {
                "proxy": {
                    "http": proxy,
                    "https": proxy
                }
            }
            webdriver_kwargs["seleniumwire_options"] = proxy_options
            self.logger.info(
                "Selenium request with proxy: %s" % proxy_options
            )

        # Load chrome driver
        browser = Chrome(**webdriver_kwargs)

        # Load target site
        retry = 0
        while retry < 2:
            # Load different branch
            if self.start_date:
                browser.get(self.sitemap_url)
            else:
                browser.get(self.base_url)

            # Wait
            time.sleep(2)

            # Increase count
            retry += 1

        # Load cookies
        cookies = browser.get_cookies()

        # Load ip
        browser.get(self.ip_url)
        time.sleep(2)

        # Load selector
        ip = None
        selector = Selector(text=browser.page_source)
        if proxy:
            ip = json.loads(
                selector.css(
                    self.ip_css
                ).extract_first()
            ).get("ip")

        # Quit browser
        browser.quit()

        return {
            c.get("name"): c.get("value") for c in cookies
        }, ip

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Update headers
        self.headers.update(
            {
                "Host": "cardingteam.cc"
            }
        )

    def start_requests(self):
        """
        :return: => request start urls if no sitemap url or no start date
                 => request sitemap url if sitemap url and start date
        """

        # Load cookies
        cookiejar = uuid.uuid1().hex
        proxy = PROXY % (
            "%s-session-%s" % (
                PROXY_USERNAME,
                cookiejar
            ),
            PROXY_PASSWORD
        )
        cookies, ip = self.get_cookies(proxy)

        if self.start_date and self.sitemap_url:
            yield Request(
                url=self.sitemap_url,
                headers=self.headers,
                cookies=cookies,
                dont_filter=True,
                callback=self.parse_sitemap,
                meta={
                    "cookiejar": cookiejar,
                    "ip": ip
                }
            )
        else:
            yield Request(
                url=self.base_url,
                headers=self.headers,
                dont_filter=True,
                cookies=cookies,
                meta={
                    "cookiejar": cookiejar,
                    "ip": ip
                }
            )

    def parse_thread_date(self, thread_date):
        return datetime.today()

    def parse_post_date(self, thread_date):
        return datetime.today()

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
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class CardingTeamScrapper(SiteMapScrapper):

    spider_class = CardingTeamSpider
    site_name = 'cardingteam.cc'
