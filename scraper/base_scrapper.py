import logging
import os
import re
import socket
import time
import uuid

import dateparser
import dateutil.parser as dparser
import requests
import scrapy

from random import choice
from glob import glob
from requests import Session
from lxml.html import fromstring
from requests.exceptions import ConnectionError
from scrapy.crawler import CrawlerProcess
from scrapy.exceptions import CloseSpider
from copy import deepcopy
from datetime import datetime
from urllib.parse import urljoin
from middlewares.utils import IpHandler
from anticaptchaofficial.recaptchav2proxyon import *
from anticaptchaofficial.recaptchav2proxyless import *
from anticaptchaofficial.hcaptchaproxyless import *
from anticaptchaofficial.hcaptchaproxyon import *
from anticaptchaofficial.imagecaptcha import *

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire.webdriver import (
    Chrome,
    ChromeOptions,
)
from scrapy import (
    Request,
    Selector
)
from base64 import (
    b64decode
)


# Vip Proxy
#VIP_PROXY_USERNAME = "lum-customer-dataviper-zone-unblocked"
#VIP_PROXY_PASSWORD = "5d2ad17825b0"
#VIP_PROXY = "http://%s:%s@zproxy.lum-superproxy.io:22225"

VIP_PROXY_USERNAME = "lum-customer-dataviper-zone-zone2"
VIP_PROXY_PASSWORD = "q37j08ih0hci"

VIP_PROXY = "http://%s:%s@zproxy.lum-superproxy.io:22225"

# Residential proxy
# PROXY_USERNAME = "lum-customer-dataviper-zone-zone2"
# PROXY_PASSWORD = "hh27g7gkk11"
# PROXY = "http://%s:%s@zproxy.lum-superproxy.io:22225"

#PROXY_USERNAME = "lum-customer-dataviper-zone-unblocked"
#PROXY_PASSWORD = "5d2ad17825b0"
#PROXY = "http://%s:%s@zproxy.lum-superproxy.io:22225"


# Luminati Proxy
PROXY_USERNAME = "lum-customer-hl_afe4c719-zone-zone1"
PROXY_PASSWORD = "8jywfhrmovdh"
PROXY = "http://%s:%s@zproxy.lum-superproxy.io:22225"


###############################################################################
# Base Scraper
###############################################################################


class BaseScrapper:

    def __init__(self, kwargs):
        self.topic_start_count = int(kwargs.get('topic_start'))\
            if kwargs.get('topic_start') else None
        self.topic_end_count = int(kwargs.get('topic_end')) + 1\
            if kwargs.get('topic_end') else None
        self.output_path = kwargs.get('output')
        self.wait_time = int(kwargs.get('wait_time'))\
            if kwargs.get('wait_time') else 1
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/71.0.3578.98 Safari/537.36'
        }
        self.session = Session()
        if kwargs.get('proxy'):
            self.session.proxies = {
                'http': kwargs.get('proxy'),
                'https': kwargs.get('proxy'),
            }
        self.avatar_name_pattern = None
        self.cloudfare_error = None
        self.retry = False
        self.ensure_avatar_path()
        if kwargs.get('daily'):
            self.ensure_daily_output_path()

    def ensure_daily_output_path(self,):
        folder_name = datetime.now().date().isoformat()
        self.output_path = f'{self.output_path}/{folder_name}'
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def ensure_avatar_path(self, ):
        self.avatar_path = f'{self.output_path}/avatars'
        if not os.path.exists(self.avatar_path):
            os.makedirs(self.avatar_path)

    def get_html_response(self, content):
        html_response = fromstring(content)
        return html_response

    def get_broken_file_topics(self,):
        broken_topics = []
        file_pattern = re.compile(r'.*/(\d+)-?1?\.html')
        for _file in glob(self.output_path+'/*'):
            topic_match = file_pattern.findall(_file)
            if topic_match and os.path.getsize(_file) < 4*1024:
                broken_topics.append(topic_match[0])
        return broken_topics

    def get_page_content(
        self,
        url,
        ignore_xpath=None,
        continue_xpath=None,
        topic=None
    ):
        try:
            response = self.session.get(url, headers=self.headers)
            content = response.content
            html_response = self.get_html_response(content)
            if ignore_xpath and html_response.xpath(ignore_xpath) and topic:
                error_file = f'{self.output_path}/{topic}.txt'
                with open(error_file, 'wb') as f:
                    return
            if continue_xpath and html_response.xpath(continue_xpath):
                return self.get_page_content(
                    url, ignore_xpath, continue_xpath)
            if self.cloudfare_error and html_response.xpath(
               self.cloudfare_error):
                if self.cloudfare_count < 5:
                    self.cloudfare_count += 1
                    time.sleep(60)
                    return self.get_page_content(
                        url, ignore_xpath, continue_xpath)
                else:
                    return
            return content
        except ConnectionError:
            if not self.retry:
                self.retry = True
                return self.get_page_content(
                    url, ignore_xpath, continue_xpath)

            return
        except:
            return

    def process_user_profile(
        self,
        uid,
        url,
    ):
        self.retry = False
        output_file = f'{self.output_path}/UID-{uid}.html'
        if os.path.exists(output_file):
            return
        time.sleep(self.wait_time)
        content = self.get_page_content(url)
        if not content:
            return
        with open(output_file, 'wb') as f:
            f.write(content)
        print(f'UID-{uid} done..!')
        return

    def process_first_page(
        self,
        topic,
        ignore_xpath=None,
        continue_xpath=None
    ):
        self.cloudfare_count = 0
        self.retry = False
        initial_file = f'{self.output_path}/{topic}-1.html'
        if os.path.exists(initial_file):
            return
        error_file = f'{self.output_path}/{topic}.txt'
        if os.path.exists(error_file):
            return
        time.sleep(self.wait_time)
        url = self.topic_url.format(topic)
        content = self.get_page_content(
            url,
            ignore_xpath,
            continue_xpath,
            topic
        )
        if not content:
            print(f'No data for url: {url}')
            return

        with open(initial_file, 'wb') as f:
            f.write(content)
        print(f'{topic}-1 done..!')
        html_response = self.get_html_response(content)
        return html_response

    def process_pagination(self, response):
        while True:
            paginated_content = self.write_paginated_data(response)
            if not paginated_content:
                return
            response = self.get_html_response(paginated_content)
            avatar_info = self.get_avatar_info(response)
            for name, url in avatar_info.items():
                self.save_avatar(name, url)

    def save_avatar(self, name, url):
        self.retry = False
        avatar_file = f'{self.avatar_path}/{name}'
        if os.path.exists(avatar_file):
            return
        time.sleep(self.wait_time)
        content = self.get_page_content(url)
        if not content:
            return
        with open(avatar_file, 'wb') as f:
            f.write(content)


class BaseTorScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super().__init__(kwargs)
        self.proxy = kwargs.get("proxy")
        if self.proxy is None:
            raise ValueError(
                "Tor scraper require tor proxy parameter. -x or --proxy"
            )


class SiteMapScrapper:

    settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
        },
        "RETRY_HTTP_CODES": [406, 429, 500],
        "RETRY_TIMES": 5,
        "LOG_ENABLED": True,
        "LOG_STDOUT": True,
        "LOG_LEVEL": "DEBUG"
    }

    time_format = "%Y-%m-%d"

    spider_class = None

    def __init__(self, kwargs):
        self.output_path = kwargs.get("output")
        self.useronly = kwargs.get("useronly")
        self.start_date = kwargs.get("start_date")
        self.firstrun = kwargs.get("firstrun")
        self.kill = kwargs.get("kill")
        self.get_users = kwargs.get("get_users")
        self.no_proxy = kwargs.get("no_proxy")
        self.proxy_countries = kwargs.get("proxy_countries")
        self.use_vip = kwargs.get("use_vip")

        self.ensure_avatar_path(kwargs.get("template"))
        if self.get_users or self.useronly:
            self.set_users_path()

        if self.kill:
            self.kill = int(self.kill)

        if self.start_date:
            try:
                self.start_date = datetime.strptime(
                    self.start_date,
                    self.time_format
                )
            except Exception as err:
                raise ValueError(
                    "Wrong date format. Correct format is: %s. Detail: %s" % (
                        self.time_format,
                        err
                    )
                )

    def load_settings(self):
        return deepcopy(self.settings)

    def load_spider_kwargs(self):
        return {
            "output_path": getattr(self, "output_path", None),
            "useronly": getattr(self, "useronly", None),
            "avatar_path": getattr(self, "avatar_path", None),
            "start_date": getattr(self, "start_date", None),
            "user_path": getattr(self, "user_path", None),
            "firstrun": getattr(self, "firstrun", None),
            "kill": getattr(self, "kill", None),
            "get_users": getattr(self, "get_users", None),
            "no_proxy": getattr(self, "no_proxy", None),
            "proxy_countries": getattr(self, "proxy_countries", None),
            "use_vip": getattr(self, "use_vip", None)
        }

    def set_users_path(self):
        self.user_path = os.path.join(
            self.output_path,
            'users'
        )
        if not os.path.exists(self.user_path):
            os.makedirs(self.user_path)

    def ensure_avatar_path(self, template):
        if getattr(self, 'site_name', None):
            self.avatar_path = f'../avatars/{self.site_name}'
        else:
            self.avatar_path = f'../avatars/{template}'
        if not os.path.exists(self.avatar_path):
            os.makedirs(self.avatar_path)

    def do_scrape(self):

        # Load process
        process = CrawlerProcess(
            self.load_settings()
        )

        # Load crawler
        crawler = process.create_crawler(self.spider_class)

        if self.load_spider_kwargs()['no_proxy']:
            crawler.spidercls.use_proxy = False
            crawler.spidercls.use_vip_proxy = False

        # Trigger running
        process.crawl(
            crawler,
            **self.load_spider_kwargs()
        )
        process.start()

        # Load stats
        stats_obj = crawler.stats
        stats_dict = crawler.stats.get_stats()

        return stats_dict


class FromDateScrapper(BaseScrapper, SiteMapScrapper):

    from_date_spider_class = None
    time_format = "%Y-%m-%d"

    def __init__(self, kwargs):
        super().__init__(kwargs)
        self.start_date = kwargs.get("start_date")
        if self.start_date:
            self.start_date = datetime.strptime(
                self.start_date,
                self.time_format
            )

    def do_scrape_from_date(self):
        process = CrawlerProcess(
            self.load_settings()
        )
        process.crawl(
            self.from_date_spider_class,
            **self.load_spider_kwargs()
        )
        process.start()



###############################################################################
# Base Spider
###############################################################################


class BypassCloudfareSpider(scrapy.Spider):

    use_proxy = True
    use_vip_proxy = False
    proxy = None
    download_delay = 0.3
    download_thread = 10
    default_useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        if (crawler.settings.frozen):
            crawler.settings.frozen = False

            # Default settings
            crawler.settings.set(
                "DEFAULT_REQUEST_HEADERS",
                {
                    "User-Agent": cls.default_useragent
                }
            )

            # Default downloader middlewares
            downloader_middlewares = {
                'scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware': 20,
                'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 40,
                'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 50,
            }

            # Proxy settings
            if cls.proxy:
                downloader_middlewares.update(
                    {
                        "middlewares.middlewares.DedicatedProxyMiddleware": 100,
                    }
                )
            elif cls.use_proxy:
                downloader_middlewares.update(
                    {
                        "middlewares.middlewares.LuminatyProxyMiddleware": 100,
                        # "middlewares.middlewares.BypassCloudfareMiddleware": 200
                    }
                )
            #else:
                #downloader_middlewares.update(
                    #{
                        #"middlewares.middlewares.BypassCloudfareMiddleware": 200
                    #}
                #)

            # Default settings
            crawler.settings.set(
                "DOWNLOADER_MIDDLEWARES",
                downloader_middlewares
            )
            crawler.settings.set(
                "DOWNLOAD_DELAY",
                cls.download_delay
            )
            crawler.settings.set(
                "CONCURRENT_REQUESTS",
                cls.download_thread
            )
            crawler.settings.set(
                "CONCURRENT_REQUESTS_PER_DOMAIN",
                cls.download_thread
            )

            # Free settings
            crawler.settings.freeze()

        spider = cls(*args, **kwargs)
        spider._set_crawler(crawler)
        return spider

    def check_bypass_success(self, browser):
        if ("blocking your access based on IP address" in browser.page_source or
                browser.find_elements_by_css_selector('.cf-error-details')):
            raise RuntimeError(f"{self.base_url} is blocking your access based on IP address.")

        element = browser.find_elements_by_xpath(self.bypass_success_xpath)
        if not bool(element):
            self.logger.info("Incorrect captcha.")
            return False
        self.logger.info("Captcha solved correctly .")
        return bool(element)

    def get_cloudflare_cookies(self, base_url=None, proxy=False, fraud_check=False):
        # Load proxy
        if self.use_vip_proxy:
            proxy_username = VIP_PROXY_USERNAME
            proxy_password = VIP_PROXY_PASSWORD
            super_proxy = VIP_PROXY
        else:
            proxy_username = PROXY_USERNAME
            proxy_password = PROXY_PASSWORD
            super_proxy = PROXY

        # Init logger
        selenium_logger = logging.getLogger("seleniumwire")
        selenium_logger.setLevel(logging.ERROR)

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

        def is_challenge_form_present(browser):
            return bool(browser.find_elements_by_class_name('challenge-form'))

        def is_hcaptcha_present(browser):
            return bool(
                browser.find_elements_by_id('cf-hcaptcha-container') and
                browser.find_elements_by_name('g-recaptcha-response') and
                browser.find_elements_by_name('h-captcha-response')
            )

        def is_i_am_human_button_present(browser):
            return browser.find_elements_by_xpath(
                '//div[@id="cf-norobot-container"]'
                '/input[@type="button" and @value="I am human!"]'
            )

        def wait(browser, timeout, wait_func):
            try:
                return WebDriverWait(browser, timeout).until(wait_func)
            except TimeoutException:
                return False

        # Loop create cookies
        while True:
            # Fraud check
            ip = None
            if fraud_check:
                ip = self.ip_handler.get_good_ip()

            # Init proxy
            if proxy:
                if ip is None:
                    proxy = super_proxy % (
                        "%s-session-%s" % (
                            proxy_username,
                            uuid.uuid1().hex
                        ),
                        proxy_password
                    )
                else:
                    proxy = super_proxy % (
                        "%s-ip-%s" % (
                            proxy_username,
                            ip
                        ),
                        proxy_password
                    )

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
            while retry < self.get_cookies_retry:
                # Load different branch
                if base_url:
                    browser.get(base_url)
                elif self.start_date and self.sitemap_url:
                    browser.get(self.sitemap_url)
                else:
                    browser.get(self.base_url)

                try:
                    success = self.check_bypass_success(browser)
                except RuntimeError:
                    success = False

                if success:
                    break

                if wait(browser, 5, is_challenge_form_present):
                    # sitekey = wait(browser, 30, wait_for_hcaptcha)
                    if wait(browser, 30,
                            lambda b: is_hcaptcha_present(b) or is_i_am_human_button_present(b)):

                        if is_i_am_human_button_present(browser):
                            time.sleep(2)
                            button = is_i_am_human_button_present(browser)[0]
                            button.send_keys(Keys.SPACE)

                        if wait(browser, 15, is_hcaptcha_present):
                            success = self.solve_cf_captcha(browser, proxy=proxy)
                            time.sleep(2)
                            break
                else:
                    break

                # Increase count
                retry += 1

            try:
                success = self.check_bypass_success(browser)
            except RuntimeError:
                success = False

            # Check extra
            if not (success and self.get_cookies_extra(browser)):
                browser.quit()
                continue

            # Load cookies
            cookies = browser.get_cookies()

            # Quit browser
            browser.quit()

            # Load ip
            request_kwargs = {
                "url": self.ip_url,
                "headers": {
                    "user-agent": self.default_useragent
                }
            }
            if proxy:
                request_kwargs["proxies"] = {
                    "http": proxy,
                    "https": proxy
                }
            data = requests.get(**request_kwargs).json()
            ip = data.get("ip")

            # Report cookies and ip
            bypass_cookies = {
                c.get("name"): c.get("value") for c in cookies
            }

            self.logger.info(
                "Bypass cookies: %s and ip: %s" % (
                    bypass_cookies,
                    ip
                )
            )

            return bypass_cookies, ip

    def solve_cf_captcha(self, browser, proxy=None, try_count=5):
        # Load selector
        selector = Selector(text=browser.page_source)

        site_key = next(iter(re.findall('sitekey=([0-9a-f\-]{36})', browser.page_source)), None)
        if not site_key:
            self.logger.info(
                "Didn't find captcha!"
            )
            return False

        for _ in range(try_count):
            # Load captcha response
            captcha_response = self.solve_hcaptcha(
                selector,
                proxy=proxy,
                site_url=browser.current_url,
                site_key=site_key,
                user_agent=browser.execute_script('return navigator.userAgent;'),
                cookies={c['name']: c['value'] for c in browser.get_cookies()}
            )

            if captcha_response:
                break
        else:
            return False

        # Display captcha box
        browser.execute_script(
            "document.querySelector(\"[name=h-captcha-response]\").setAttribute(\"style\",\"display: block\")"
        )
        browser.execute_script(
            "document.querySelector(\"[name=g-recaptcha-response]\").setAttribute(\"style\",\"display: block\")"
        )

        # Input captcha response
        browser.execute_script(
            "document.querySelector(\"[name=h-captcha-response]\").innerText = \"%s\"" % captcha_response
        )
        browser.execute_script(
            "document.querySelector(\"[name=g-recaptcha-response]\").innerText = \"%s\"" % captcha_response
        )

        browser.find_element_by_class_name('challenge-form').submit()

        return True


class SitemapSpider(BypassCloudfareSpider):

    # Url stuffs
    base_url = None
    sitemap_url = None
    ip_url = "https://api.ipify.org?format=json"

    # anticaptcha api #
    captcha_token = "d7da71f33665a41fca21ecd11dc34015"
    captcha_instruction = "All character in picture"

    # Payload stuffs
    post_headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Format stuff
    sitemap_datetime_format = "%Y-%m-%dT%H:%MZ"  # Date time format of majority of sitemap lastmod/thread last update time #
    post_datetime_format = "%m-%d-%Y"  # Date time format of majority of post update time #

    # Css stuffs
    ip_css = "pre::text"

    # Xpath stuffs

    # Forum xpath #
    forum_sitemap_xpath = None  # Xpath of forum url in the forum sitemap #
    forum_xpath = None  # Xpath of forum url in the main entry forum #
    pagination_xpath = None  # Xpath of next button in forum detail #

    # Thread xpath #
    thread_sitemap_xpath = None  # Xpath of the whole block of thread in thread sitemap #
    thread_url_xpath = None  # Xpath of thread url in thread sitemap #
    thread_lastmod_xpath = None  # Xpath of thread lastmod in thread sitemap #

    thread_xpath = None
    thread_first_page_xpath = None  # Xpath of thread url in forum detail #
    thread_last_page_xpath = None  # Xpath of thread url last page in forum detail (if exist) #
    thread_date_xpath = None  # Xpath of thread last post update time in forum detail #
    thread_page_xpath = None  # Xpath of current page button in thread detail #
    thread_pagination_xpath = None  # Xpath of previous button in thread pagination #

    # Post xpath #
    post_date_xpath = None  # Xpath of post update time in thread detail #

    # Avatar xpath #
    avatar_xpath = None  # Xpath to define location of avatar url #

    # Recaptcha regular xpath #
    recaptcha_site_key_xpath = None  # Xpath to get recaptcha site key #
    hcaptcha_site_key_xpath = None  # Xpath to get hcaptcha site key #

    # Other settings
    get_cookies_delay = 2
    get_cookies_retry = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Init stuffs
        self.output_path = kwargs.get("output_path")
        self.useronly = kwargs.get("useronly")
        self.avatar_path = kwargs.get("avatar_path")
        self.user_path = kwargs.get("user_path")
        self.start_date = kwargs.get("start_date")
        self.kill = kwargs.get("kill")
        self.get_users = kwargs.get("get_users")
        self.topic_pages_saved = 0
        self.forums = set()
        self.topics = set()
        self.topics_scraped = set()
        self.avatars = set()

        if kwargs.get("no_proxy") is not None:
            self.use_proxy = False
            self.use_vip_proxy = False

        if kwargs.get("proxy_countries") is not None:
            self.proxy_countries = kwargs["proxy_countries"]

        if kwargs.get("use_vip") is not None:
            # self.use_proxy = False
            self.use_vip_proxy = True

        # Load fraud check settings

        self.ip_handler = IpHandler(
            logger=self.logger,
            fraudulent_threshold=getattr(self, "fraudulent_threshold", 50),
            ip_batch_size=getattr(self, "ip_batch_size", 20),
            use_vip_proxy=self.use_vip_proxy
        )

        # Handle headers
        self.headers = {
            "User-Agent": self.default_useragent
        }
        self.post_headers.update(self.headers)

        # Handle cookies
        self.cookies = kwargs.get("cookies")
        if self.cookies:
            self.cookies = self.load_cookies(self.cookies)

        # Handle code file
        root_folder = os.path.dirname(os.path.abspath(__file__))
        self.backup_code_file = os.path.join(
            root_folder,
            '../code',
            self.name
        )
        if not os.path.exists(self.backup_code_file):
            self.backup_code_file = None
            self.backup_codes = []
        else:
            with open(
                file=self.backup_code_file,
                mode="r",
                encoding="utf-8"
            ) as file:
                self.backup_codes = [
                    code.strip() for code in file.read().split("\n")
                ]

    def write_backup_codes(self):
        with open(
            file=self.backup_code_file,
            mode="w+",
            encoding="utf-8"
        ) as file:
            file.write(
                "\n".join(self.backup_codes)
            )

    def synchronize_headers(self, response):
        self.headers.update(
            {
                "User-Agent": response.request.headers.get("User-Agent")
            }
        )

    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip", "proxy"]
            if response.meta.get(key)
        }

        meta.update(default_meta)

        return meta

    def extract_thread_stats(self, thread):
        """
        :param thread: str => thread html contain url and last mod
        :return: thread url: str, thread lastmod: datetime
        """
        # Load selector
        # selector = Selector(text=thread)

        # Load stats
        thread_first_page_url = None
        if self.thread_first_page_xpath:
            thread_first_page_url = thread.xpath(
                self.thread_first_page_xpath
            ).extract_first()

        thread_last_page_url = None
        if self.thread_last_page_xpath:
            thread_last_page_url = thread.xpath(
                self.thread_last_page_xpath
            ).extract_first()

        thread_lastmod = thread.xpath(
            self.thread_date_xpath
        ).extract_first()

        # Process stats
        try:
            thread_url = (self.parse_thread_url(thread_last_page_url)
                          or self.parse_thread_url(thread_first_page_url))
        except Exception as err:
            thread_url = None

        try:
            thread_lastmod = self.parse_thread_date(thread_lastmod)
        except Exception as err:
            thread_lastmod = None

        return thread_url, thread_lastmod

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        try:
            return dateparser.parse(thread_date).replace(tzinfo=None)
        except:
            return datetime.strptime(
                thread_date.strip(),
                self.post_datetime_format
            )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        try:
            return dateparser.parse(post_date).replace(tzinfo=None)
        except:
            return datetime.strptime(
                post_date.strip(),
                self.post_datetime_format
            )

    def parse_thread_url(self, thread_url):
        """
        :param thread_url: str => thread url as string
        :return: str => thread url as string
        """
        if thread_url:
            return thread_url.strip()
        else:
            return

    def get_topic_id(self, url=None):
        """
        :param url: str => thread url
        :return: str => extracted topic id from thread url
        """
        if getattr(self, "topic_pattern", None):
            try:
                return self.topic_pattern.findall(url)[0]
            except Exception as err:
                return

        topic_id = str(
            int.from_bytes(
                url.encode('utf-8'),
                byteorder='big'
            ) % (10 ** 7)
        )

        return topic_id

    def get_avatar_file(self, url=None):
        """
        :param url: str => avatar url
        :return: str => extracted avatar file from avatar url
        """

        if getattr(self, "avatar_name_pattern", None):
            try:
                file_name = os.path.join(
                    self.avatar_path,
                    self.avatar_name_pattern.findall(url)[0]
                )
                extensions = ['jpg', 'jpeg', 'png', 'gif']
                for ext in extensions:
                    if ext in file_name:
                        return file_name
                return f'{file_name}.jpg'
            except Exception as err:
                return

        return

    def get_existing_file_date(self, topic_id):

        ## Load first page file name
        #file_name = os.path.join(
            #self.output_path,
            #"%s-1.html" % topic_id
        #)

        ## If file name exist then return
        #if not os.path.exists(file_name):
            #return

        last_scrape_datetimes = [
            datetime.fromtimestamp(
                os.stat(os.path.join(self.output_path, fn)).st_mtime
            )
            for fn in os.listdir(self.output_path)
            if re.match(r'%s-\d{1,3}\.html' % topic_id, fn)
        ]

        if last_scrape_datetimes:
            return max(last_scrape_datetimes)

        ## Else return time stamp
        # created_ts = os.stat(file_name).st_mtime
        # return datetime.fromtimestamp(created_ts)

    def check_existing_file_date(self, **kwargs):
        # Load variables
        topic_id = kwargs.get("topic_id")
        thread_date = kwargs.get("thread_date")
        thread_url = kwargs.get("thread_url")

        # Check existing file date
        existing_file_date = self.get_existing_file_date(topic_id)
        if existing_file_date and thread_date and existing_file_date > thread_date:
            self.logger.info(
                f"Thread {thread_url} ignored because existing "
                f"file is already latest. Last Scraped: {existing_file_date}"
            )
            return True

        return False

    def load_cookies(self, cookies_string):
        """
        :param cookies_string: str => Cookie string as in browser header
        :return: dict => Cookies as dict type, using in scrapy request
        """
        cookies_elements = [
            element.strip().split("=") for element in cookies_string.split(";")
        ]
        cookies = {
            element[0]: "=".join(element[1:]) for element in cookies_elements
        }
        return cookies

    def load_proxies(self, response):
        """
        :param response: scrapy response => response to extract proxy from
        :return: str => proxy to use for other requests
        """

        # Init proxy
        proxy = None

        # Check proxy settings
        meta_proxy = response.request.meta.get("proxy")
        if meta_proxy:
            proxy = meta_proxy

        # Check proxy authentication settings
        request = response.request
        basic_auth = request.headers.get("Proxy-Authorization")
        if basic_auth:
            # Decode proxy username and password
            basic_auth_encoded = basic_auth.decode("utf-8").split()[1]
            username, password = b64decode(basic_auth_encoded).decode("utf-8").split(":")

            # Standardize proxy
            root_proxy = meta_proxy.replace(
                "https://", ""
            ).replace(
                "http://", ""
            )

            # Generate authentication proxy
            proxy = "%s:%s@%s" % (
                username,
                password,
                root_proxy
            )

        return proxy

    # Main method to solve all kind of captcha: recaptcha #
    
    def solve_hcaptcha(self, response, proxy=None, site_url=None, site_key=None, user_agent=None,
                       cookies=None):
        """
        :param response: scrapy response => response that contains regular recaptcha
        :return: str => recaptcha solved token to submit login
        """
        solver = hCaptchaProxyless()

        # Load proxy
        if proxy is None:
            try:
                proxy = self.load_proxies(response)
            except Exception as err:
                proxy = None

        if proxy:
            # Trim prototal
            proxy = proxy.replace(
                "https://", ""
            ).replace(
                "http://", ""
            )
            # Load authen vs domain part
            user_pwd, host_port = proxy.split('@')

            # Load solver with proxy
            solver = hCaptchaProxyon()

            address, port = host_port.split(":")
            valid_ip_address_regex = (
                r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|"
                r"[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
            )
            if re.match(valid_ip_address_regex, address) is None:
                from socket import gethostbyname
                address = gethostbyname(address)

            solver.set_proxy_address(address)
            solver.set_proxy_port(int(port))
            solver.set_proxy_login(user_pwd.split(":")[0])
            solver.set_proxy_password(user_pwd.split(":")[1])
            solver.set_user_agent(user_agent)
            solver.set_proxy_type('http')

            if cookies:
                cookies = '; '.join(['='.join(c) for c in cookies.items()])
                solver.set_cookies(cookies)

        # Init site url and key
        if site_url is None:
            site_url = response.url

        # get site-key if not provided
        if not site_key:
            site_key = response.xpath(self.hcaptcha_site_key_xpath).extract_first()

        # Init solver params
        solver.set_verbose(1)
        solver.set_key(self.captcha_token)
        solver.set_website_url(site_url)
        solver.set_website_key(site_key)

        # Solve and return h response
        h_response = solver.solve_and_return_solution()
        if h_response != 0:
            return h_response
        else:
            return ''

    # Main method to solve all kind of captcha: recaptcha #
    
    def solve_recaptcha(self, response, proxyless=False):
        """
        :param response: scrapy response => response that contains regular recaptcha
        :return: str => recaptcha solved token to submit login
        """

        # Load proxy
        proxy = self.load_proxies(response)
        if proxy and not proxyless:
            solver = recaptchaV2Proxyon()

            user_pwd, host_port = proxy.split('@')
            hostname, port = host_port.split(":")
            host = socket.gethostbyname(hostname)

            solver.set_proxy_address(host)
            solver.set_proxy_port(port)
            solver.set_proxy_login(user_pwd.split(":")[0])
            solver.set_proxy_password(user_pwd.split(":")[1])
            solver.set_user_agent(response.request.headers['user-agent'].decode('utf-8'))
        else:
            solver = recaptchaV2Proxyless()

        # Init site url and key
        site_url = response.url
        site_key = response.xpath(self.recaptcha_site_key_xpath).extract_first()

        solver.set_verbose(1)
        solver.set_key(self.captcha_token)
        solver.set_website_url(site_url)
        solver.set_website_key(site_key)

        g_response = solver.solve_and_return_solution()
        if g_response != 0:
            return g_response
        else:
            return ''

    def solve_captcha(self, image_url, response, cookies={}, headers={}):
        solver = imagecaptcha()
        solver.set_verbose(1)
        solver.set_key(self.captcha_token)

        # Load cookies from request
        try:
            cookies.update(
                self.load_cookies(
                    response.request.headers.get("Cookie").decode("utf-8")
                )
            )
        except Exception as err:
            pass

        # Load cookies from response
        try:
            cookies.update(
                self.load_cookies(
                    response.headers.get("Set-Cookie").decode("utf-8")
                )
            )
        except Exception as err:
            pass

        # Load proxy
        if response:
            proxy = self.load_proxies(response)

        # Load user agent
        user_agent = self.headers.get("User-Agent")
        if response:
            user_agent = response.request.headers.get("User-Agent")

        # Update headers
        headers.update(
            {
                "User-Agent": user_agent
            }
        )

        # Download content
        try:
            image_content = self.get_captcha_image_content(
                image_url, cookies, headers, proxy)
        except Exception as err:
            image_content = b64decode(image_url)

        # Archive captcha content
        root_folder = os.path.dirname(os.path.abspath(__file__))
        captcha_folder = os.path.join(root_folder, '../captcha')
        if not os.path.exists(captcha_folder):
            os.makedirs(captcha_folder)
        with open(f"{captcha_folder}/captcha.png", "wb") as file:
            file.write(image_content)

        captcha_text = solver.solve_and_return_solution(f"{captcha_folder}/captcha.png")
        if captcha_text != 0:
            return captcha_text.replace(' ', '')
        else:
            return ''

    def get_captcha_image_content(self, image_url, cookies={}, headers={}, proxy=None):
        # Load session
        session = requests.Session()
        if proxy:
            session.proxies = {
                "http": proxy,
                "https": proxy
            }

        # Set cookies to session
        for name, value in cookies.items():
            session.cookies.set(name, value)

        response = session.get(
            image_url,
            headers=headers
        )
        self.logger.info(
            "Download captcha image content with headers %s" % response.request.headers
        )
        return response.content

    def get_blockchain_domain(self, domain):
        # Get domain root only
        domain = domain.split('/')[2] if '://' in domain else domain

        # List of apis and load api
        apis = ['https://bdns.co/r/', 'https://bdns.us/r/', 'https://bdns.bz/r/']

        while True:
            api = choice(apis)

            # Load domain ip
            try:
                r = requests.get(api+domain)
                if r.status_code == 200:
                    ip = r.text.splitlines()[0]
                    return ip
                else:
                    return
            except Exception as err:
                continue

    def start_requests(self, cookiejar=None, ip=None):
        """
        :return: => request start urls if no sitemap url or no start date
                 => request sitemap url if sitemap url and start date
        """

        # Load meta
        meta = {}
        if cookiejar:
            meta["cookiejar"] = cookiejar
        if ip:
            meta["ip"] = ip

        # Branch choices requests
        if self.start_date and self.sitemap_url:
            yield scrapy.Request(
                url=self.sitemap_url,
                headers=self.headers,
                callback=self.parse_sitemap,
                dont_filter=True,
                meta=meta
            )
        else:
            yield Request(
                url=self.base_url,
                headers=self.headers,
                dont_filter=True,
                meta=meta
            )

    def parse_sitemap(self, response):
        """
        :param response: scrapy response => Level 1, forum sitemap
        :return:
        """

        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Load selector
        selector = Selector(text=response.text)

        # Load forum
        all_forum = selector.xpath(self.forum_sitemap_xpath).extract()

        for forum in all_forum:
            yield Request(
                url=forum,
                headers=self.headers,
                callback=self.parse_sitemap_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_sitemap_forum(self, response):
        """
        :param response: scrapy response => Level 2, thread sitemap
        :return:
        """

        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Load selector
        selector = Selector(text=response.text)

        # Load thread
        all_threads = selector.xpath(self.thread_sitemap_xpath).extract()

        for thread in all_threads:
            yield from self.parse_sitemap_thread(
                thread,
                response
            )

    def parse_sitemap_thread(self, thread, response):
        """
        :param thread: str => thread html include url and last mod
        :param response: scrapy response => scrapy response
        :return:
        """

        # Load selector
        selector = Selector(text=thread)

        # Load thread url and update
        thread_url = self.parse_thread_url(
            selector.xpath(self.thread_url_xpath).extract_first()
        )
        if not thread_url:
            return
        thread_date = self.parse_thread_date(
            selector.xpath(self.thread_lastmod_xpath).extract_first()
        )

        if self.start_date > thread_date.replace(tzinfo=None):
            self.logger.info(
                "Thread %s ignored because last update in the past. Detail: %s" % (
                    thread_url,
                    thread_date
                )
            )
            return

        # Get topic id
        topic_id = self.get_topic_id(thread_url)
        if not topic_id:
            return

        # Check file exist
        if self.check_existing_file_date(
            topic_id=topic_id,
            thread_date=thread_date,
            thread_url=thread_url
        ):
            return

        # Load request arguments
        request_arguments = {
            "url": thread_url,
            "headers": self.headers,
            "callback": self.parse_thread,
            "meta": self.synchronize_meta(
                response,
                default_meta={
                    "topic_id": topic_id
                }
            )
        }
        if self.cookies:
            request_arguments["cookies"] = self.cookies

        yield Request(**request_arguments)

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = set(response.xpath(self.forum_xpath).extract())

        # update stats
        self.crawler.stats.set_value("forum/forum_count", len(all_forums))

        for forum_url in all_forums:
            yield response.follow(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_forum(self, response, thread_meta={}, is_first_page=True):

        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        self.logger.info(
            "Next_page_url: %s" % response.url
        )

        threads = response.xpath(self.thread_xpath)

        lastmod_pool = []
        for thread in threads:
            thread_url, thread_lastmod = self.extract_thread_stats(thread)
            if not thread_url:
                self.crawler.stats.inc_value("forum/thread_no_url_count")
                self.logger.warning(
                    "Unable to find thread URL on the forum: %s",
                    response.url
                )
                continue

            # Parse topic id
            topic_id = self.get_topic_id(thread_url)
            if not topic_id:
                self.crawler.stats.inc_value("forum/thread_no_topic_id_count")
                self.logger.warning(
                    "Unable to find topic ID of the thread: %s",
                    response.join(thread_url)
                )
                continue

            if thread_lastmod is None:
                if topic_id not in self.topics:
                    self.topics.add(topic_id)
                    self.crawler.stats.inc_value("forum/thread_no_date_count")
                    self.crawler.stats.set_value("forum/thread_count", len(self.topics))

                if self.start_date:
                    self.logger.info(
                        "Date not found in thread %s " % thread_url
                    )
                    continue
            else:
                lastmod_pool.append(thread_lastmod)

            # If start date, check last mod
            if self.start_date and thread_lastmod < self.start_date:
                if topic_id not in self.topics:
                    self.topics.add(topic_id)
                    self.crawler.stats.inc_value("forum/thread_outdated_count")
                    self.crawler.stats.set_value("forum/thread_count", len(self.topics))

                self.logger.info(
                    "Thread %s last updated is %s before start date %s. Ignored." % (
                        thread_url, thread_lastmod, self.start_date
                    )
                )
                continue

            # Standardize thread url only if it is not complete url
            if 'http://' not in thread_url and 'https://' not in thread_url:
                temp_url = thread_url
                if self.base_url not in thread_url:
                    temp_url = response.urljoin(thread_url)

                if self.base_url not in temp_url:
                    temp_url = self.base_url + thread_url

                thread_url = temp_url

            # Check file exist
            if self.check_existing_file_date(
                    topic_id=topic_id,
                    thread_date=thread_lastmod,
                    thread_url=thread_url
            ):
                # update stats
                if topic_id not in self.topics:
                    self.topics.add(topic_id)
                    self.crawler.stats.inc_value("forum/thread_already_scraped_count")
                    self.crawler.stats.set_value("forum/thread_count", len(self.topics))

                continue

            # Check thread meta
            if thread_meta:
                meta = thread_meta
            else:
                meta = self.synchronize_meta(response)

            # Update topic id
            meta["topic_id"] = topic_id

            # update stats
            self.topics.add(topic_id)
            self.crawler.stats.set_value("forum/thread_count", len(self.topics))

            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta=meta
            )

        # Pagination
        if not lastmod_pool:
            self.crawler.stats.inc_value("forum/forum_no_threads_count")
            self.logger.info(
                "Forum without thread, exit: %s",
                response.url
            )
            return

        # update stats
        if is_first_page:
            self.crawler.stats.inc_value("forum/forum_processed_count")

        if self.start_date and self.start_date > max(lastmod_pool):
            self.logger.info(
                "Found no more thread update later than %s in forum %s. Exit." % (
                    self.start_date,
                    response.url
                )
            )
            return
        next_page = self.get_forum_next_page(response)
        if next_page:
            yield Request(
                url=next_page,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
                cb_kwargs={'is_first_page': False}
            )

    def get_forum_next_page(self, response):
        next_page = response.xpath(self.pagination_xpath).extract_first()
        if not next_page:
            return
        next_page = next_page.strip()

        if 'http://' not in next_page and 'https://' not in next_page:
            temp_url = next_page
            if self.base_url not in next_page:
                temp_url = response.urljoin(next_page)

            if self.base_url not in temp_url:
                temp_url = self.base_url + next_page

            next_page = temp_url

        return next_page

    def parse_thread(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Get topic id
        topic_id = response.meta.get("topic_id")

        # Load all post date
        post_dates = [
            self.parse_post_date(post_date) for post_date in
            response.xpath(self.post_date_xpath).extract()
            if post_date.strip() and self.parse_post_date(post_date)
        ]

        if self.start_date and not post_dates:
            if topic_id not in self.topics_scraped:
                self.crawler.stats.inc_value("forum/thread_no_messages_count")

            self.logger.info('No dates found in thread')
            return

        if self.start_date and max(post_dates) < self.start_date:
            if topic_id not in self.topics_scraped:
                self.crawler.stats.inc_value("forum/thread_outdated_count")

            self.logger.info(
                "No more post to update."
            )
            return

        # Save thread content
        if not self.useronly:
            current_page = self.get_thread_current_page(response)
            with open(
                file=os.path.join(
                    self.output_path,
                    "%s-%s.html" % (
                        topic_id,
                        current_page
                    )
                ),
                mode="w+",
                encoding="utf-8"
            ) as file:
                file.write(response.text)
            self.logger.info(
                f'{topic_id}-{current_page} done..!'
            )
            self.topic_pages_saved += 1

            # Update stats
            self.topics_scraped.add(topic_id)
            self.crawler.stats.set_value(
                "forum/thread_saved_count",
                len(self.topics_scraped)
            )

            # Kill task if kill count met
            if self.kill and self.topic_pages_saved >= self.kill:
                raise CloseSpider(reason="Kill count met, shut down.")

        # Thread pagination
        next_page = self.get_thread_next_page(response)
        if next_page:

            yield Request(
                url=next_page,
                headers=self.headers,
                callback=self.parse_thread,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "topic_id": topic_id
                    }
                )
            )

    def get_thread_current_page(self, response):
        current_page = response.xpath(
                self.thread_page_xpath
        ).extract_first() or "1"
        return current_page

    def get_thread_next_page(self, response):
        next_page = response.xpath(self.thread_pagination_xpath).extract_first()
        if not next_page:
            return

        next_page = next_page.strip()
        # process url if its not complete
        if 'http://' not in next_page and 'https://' not in next_page:
            temp_url = next_page

            if self.base_url not in next_page:
                temp_url = response.urljoin(next_page)

            if self.base_url not in temp_url:
                temp_url = self.base_url + next_page

            next_page = temp_url

        return next_page

    def parse_avatars(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Save avatar content
        all_avatars = set(response.xpath(self.avatar_xpath).extract())

        for avatar_url in all_avatars:
            # Standardize avatar url only if its not complete url
            slash = False
            if 'http://' not in avatar_url and 'https://' not in avatar_url:
                temp_url = avatar_url

                if avatar_url.startswith('//'):
                    slash = True
                    temp_url = avatar_url[2:]

                if not avatar_url.lower().startswith("http"):
                    temp_url = response.urljoin(avatar_url)

                if self.base_url not in temp_url and not slash:
                    temp_url = self.base_url + avatar_url

                avatar_url = temp_url

            if 'image/svg' in avatar_url:
                continue

            file_name = self.get_avatar_file(avatar_url)

            if file_name is None:
                continue

            if os.path.exists(file_name):
                continue

            # update stats
            self.avatars.add(avatar_url)
            self.crawler.stats.set_value("forum/avatar_count", len(self.avatars))

            yield Request(
                url=avatar_url,
                headers=self.headers,
                callback=self.parse_avatar,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "file_name": file_name
                    }
                ),
            )

    def parse_avatar(self, response):

        # Load file name
        file_name = response.meta.get("file_name")
        avatar_name = os.path.basename(file_name)

        # Save avatar
        with open(file_name, "wb") as f:
            f.write(response.body)
            self.logger.info(
                f"Avatar {avatar_name} done..!"
            )

        self.crawler.stats.inc_value("forum/avatar_saved_count")

    def solve_cookies_captcha(self, browser, proxy=None):
        return browser, True

    def get_cookies_extra(self, browser):
        return True

    def get_cookies(self, base_url=None, proxy=False, fraud_check=False, check_captcha=False):

        # Load proxy
        if self.use_vip_proxy:
            proxy_username = VIP_PROXY_USERNAME
            proxy_password = VIP_PROXY_PASSWORD
            super_proxy = VIP_PROXY
        else:
            proxy_username = PROXY_USERNAME
            proxy_password = PROXY_PASSWORD
            super_proxy = PROXY

        # Init logger
        selenium_logger = logging.getLogger("seleniumwire")
        selenium_logger.setLevel(logging.ERROR)

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

        # Loop create cookies
        while True:
            # Fraud check
            ip = None
            if fraud_check:
                ip = self.ip_handler.get_good_ip()

            # Init proxy
            if proxy:
                if ip is None:
                    proxy = super_proxy % (
                        "%s-session-%s" % (
                            proxy_username,
                            uuid.uuid1().hex
                        ),
                        proxy_password
                    )
                else:
                    proxy = super_proxy % (
                        "%s-ip-%s" % (
                            proxy_username,
                            ip
                        ),
                        proxy_password
                    )

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
            while retry < self.get_cookies_retry:
                # Load different branch
                if base_url:
                    browser.get(base_url)
                elif self.start_date and self.sitemap_url:
                    browser.get(self.sitemap_url)
                else:
                    browser.get(self.base_url)

                # Solve captcha if exist such requirements
                if check_captcha:
                    browser, success = self.solve_cookies_captcha(browser)
                    if not success:
                        browser.quit()
                        break

                # Wait
                time.sleep(self.get_cookies_delay)

                # Increase count
                retry += 1

            # Check if captcha and success
            if check_captcha and not success:
                continue

            # Check extra
            success = self.get_cookies_extra(browser)
            if not success:
                browser.quit()
                continue

            # Load cookies
            cookies = browser.get_cookies()

            # Quit browser
            browser.quit()

            # Load ip
            request_kwargs = {
                "url": self.ip_url,
                "headers": {
                    "user-agent": self.default_useragent
                }
            }
            if proxy:
                request_kwargs["proxies"] = {
                    "http": proxy,
                    "https": proxy
                }
            data = requests.get(**request_kwargs).json()
            ip = data.get("ip")

            # Report cookies and ip
            bypass_cookies = {
                c.get("name"): c.get("value") for c in cookies
            }

            self.logger.info(
                "Bypass cookies: %s and ip: %s" % (
                    bypass_cookies,
                    ip
                )
            )

            return bypass_cookies, ip


class MarketPlaceSpider(SitemapSpider):
    market_url_xpath = None
    product_url_xpath = None
    next_page_xpath = None
    user_xpath = None

    def get_market_url(self, url):
        if self.base_url not in url:
            url = self.base_url + url
        return url

    def get_product_url(self, url):
        if self.base_url not in url:
            url = self.base_url + url
        return url

    def get_user_url(self, url):
        if self.base_url not in url:
            url = self.base_url + url
        return url

    def get_avatar_url(self, url):
        if self.base_url not in url:
            url = self.base_url + url
        return url

    def get_user_id(self, url):
        return url.rsplit('/', 1)[-1]

    def get_file_id(self, url):
        return url.rsplit('/', 1)[-1]

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        urls = response.xpath(self.market_url_xpath).extract()
        for url in urls:
            url = self.get_market_url(url)
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_products,
                meta=self.synchronize_meta(response),
            )

    def parse_products(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        self.logger.info('next_page_url: {}'.format(response.url))
        products = response.xpath(self.product_url_xpath).extract()
        for product_url in products:
            product_url = self.get_product_url(product_url)
            file_id = self.get_file_id(product_url)
            file_name = '{}/{}.html'.format(self.output_path, file_id)
            if os.path.exists(file_name):
                continue
            yield Request(
                url=product_url,
                headers=self.headers,
                callback=self.parse_product,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        'file_id': file_id
                    }
                )
            )

        next_page_url = response.xpath(self.next_page_xpath).extract_first()
        if next_page_url:
            next_page_url = self.get_market_url(next_page_url)
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_products,
                meta=self.synchronize_meta(response),
            )

    def parse_product(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        file_id = response.meta['file_id']
        file_name = '{}/{}.html'.format(self.output_path, file_id)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'Product: {file_id} done..!')

        if not self.user_xpath:
            return
        user_url = response.xpath(self.user_xpath).extract_first()
        if not user_url:
            return
        user_url = self.get_user_url(user_url)
        user_id = self.get_user_id(user_url)
        file_name = '{}/{}.html'.format(self.user_path, user_id)
        if os.path.exists(file_name):
            return
        yield Request(
            url=user_url,
            headers=self.headers,
            callback=self.parse_user,
            meta=self.synchronize_meta(
                response,
                default_meta={
                    'file_name': file_name,
                    'user_id': user_id
                }
            )
        )

    def parse_user(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        user_id = response.meta['user_id']
        file_name = response.meta['file_name']
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'User: {user_id} done..!')

        avatar_url = response.xpath(self.avatar_xpath).extract_first()
        if not avatar_url:
            return
        avatar_url = self.get_avatar_url(avatar_url)
        ext = avatar_url.rsplit('.', 1)[-1]
        if not ext:
            ext = 'jpg'
        file_name = '{}/{}.{}'.format(self.avatar_path, user_id, ext)
        if os.path.exists(file_name):
            return
        yield Request(
            url=avatar_url,
            headers=self.headers,
            callback=self.parse_avatar,
            meta=self.synchronize_meta(
                response,
                default_meta={
                    'file_name': file_name,
                    'user_id': user_id
                }
            )
        )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        with open(file_name, 'wb') as f:
            f.write(response.body)
            self.logger.info(
                f"Avatar for user {response.meta['user_id']} done..!")


class SeleniumSpider(SitemapSpider):
    ban_text = ''
    skip_forums = None

    def parse_start(self):
        response = fromstring(self.browser.page_source)
        all_forums = response.xpath(self.forum_xpath)
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            if self.skip_forums and any(
             forum_url.endswith(i) for i in self.skip_forums):
                continue
            self.process_forum(forum_url)
            time.sleep(self.delay)

        self.browser.quit()

    def process_forum(self, forum_url):
        self.browser.get(forum_url)
        response = fromstring(self.browser.page_source)
        if self.ban_text and self.ban_text in self.browser.page_source.lower():
            raise CloseSpider(reason="Account is banned")
        self.logger.info(f"Next_page_url: {forum_url}")
        threads = response.xpath(self.thread_xpath)
        lastmod_pool = []
        for thread in threads:
            thread_url, thread_lastmod = self.extract_thread_stats(thread)
            if not thread_url:
                continue

            if self.start_date and thread_lastmod is None:
                self.logger.info(
                    "Last update date not found in Thread %s, "
                    "so ignored." % thread_url
                )
                continue

            lastmod_pool.append(thread_lastmod)

            # If start date, check last mod
            if self.start_date and thread_lastmod < self.start_date:
                self.logger.info(
                    "Thread %s last updated is %s before start date %s. "
                    "Ignored." % (thread_url, thread_lastmod, self.start_date)
                )
                continue

            # Standardize thread url
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url

            # Parse topic id
            try:
                topic_id = self.topic_pattern.findall(thread_url)[0]
            except Exception:
                continue

            # Check file exist
            if self.check_existing_file_date(
                    topic_id=topic_id,
                    thread_date=thread_lastmod,
                    thread_url=thread_url
            ):
                continue

            self.parse_thread(thread_url, topic_id)

        # Pagination
        if not lastmod_pool:
            self.logger.info(
                "Forum without thread, exit."
            )
            return

        if self.start_date and self.start_date > max(lastmod_pool):
            self.logger.info(
                "Found no more thread update later than %s in forum %s. "
                "Exit." % (self.start_date, forum_url)
            )
            return
        next_page = self.get_forum_next_page(response)
        if next_page:
            self.process_forum(next_page)

    def extract_thread_stats(self, thread):

        # Load stats
        thread_first_page_url = None
        if self.thread_first_page_xpath:
            thread_first_page_url = thread.xpath(
                self.thread_first_page_xpath
            )

        thread_last_page_url = None
        if self.thread_last_page_xpath:
            thread_last_page_url = thread.xpath(
                self.thread_last_page_xpath
            )

        thread_lastmod = thread.xpath(
            self.thread_date_xpath
        )

        # Process stats
        if thread_last_page_url:
            thread_url = thread_last_page_url[0]
        elif thread_first_page_url:
            thread_url = thread_first_page_url[0]
        else:
            thread_url = None

        try:
            thread_lastmod = dateparser.parse(thread_lastmod[0].strip())
        except Exception as err:
            thread_lastmod = None

        return thread_url, thread_lastmod

    def get_forum_next_page(self, response):
        next_page = response.xpath(self.pagination_xpath)
        if not next_page:
            return
        next_page = next_page[0].strip()
        temp_url = next_page

        if self.base_url not in next_page:
            temp_url = urljoin(self.base_url, next_page)

        if self.base_url not in temp_url:
            temp_url = self.base_url + next_page

        next_page = temp_url

        return next_page

    def parse_thread(self, thread_url, topic_id):
        time.sleep(self.delay)
        self.browser.get(thread_url)
        response = fromstring(self.browser.page_source)
        if self.ban_text and self.ban_text in self.browser.page_source.lower():
            raise CloseSpider(reason="Account is banned")
        post_dates = [
            dateparser.parse(post_date.strip()) for post_date in
            response.xpath(self.post_date_xpath)
            if post_date.strip() and dateparser.parse(post_date.strip())
        ]
        if self.start_date and max(post_dates) < self.start_date:
            self.logger.info(
                "No more post to update."
            )
            return

        current_page = self.get_thread_current_page(response)
        with open(
            file=os.path.join(
                self.output_path,
                "%s-%s.html" % (topic_id, current_page)
            ),
            mode="w+",
            encoding="utf-8"
        ) as file:
            file.write(self.browser.page_source)
            self.logger.info(
                f'{topic_id}-{current_page} done..!'
            )
            self.topic_pages_saved += 1

            # Update stats
            self.crawler.stats.set_value(
                "topic pages saved",
                self.topic_pages_saved
            )

            # Kill task if kill count met
            if self.kill and self.topic_pages_saved >= self.kill:
                raise CloseSpider(reason="Kill count met, shut down.")
        self.parse_avatars(response)
        next_page = self.get_thread_next_page(response)
        if next_page:
            self.parse_thread(next_page, topic_id)

    def get_thread_current_page(self, response):
        current_page = response.xpath(self.thread_page_xpath)
        return current_page[0] if current_page else '1'

    def get_thread_next_page(self, response):
        next_page = response.xpath(self.thread_pagination_xpath)
        if not next_page:
            return
        next_page = next_page[0].strip()

        if 'http://' not in next_page and 'https://' not in next_page:
            temp_url = next_page

            if self.base_url not in next_page:
                temp_url = urljoin(self.base_url, next_page)

            if self.base_url not in temp_url:
                temp_url = self.base_url + next_page

            next_page = temp_url

        return next_page

    def parse_avatars(self, response):

        # Save avatar content
        all_avatars = response.xpath(self.avatar_xpath)
        for avatar_url in all_avatars:

            temp_url = avatar_url
            # Standardize avatar url
            if not avatar_url.lower().startswith("http"):
                temp_url = urljoin(self.base_url, avatar_url)

            if self.base_url not in temp_url:
                temp_url = self.base_url + avatar_url

            avatar_url = temp_url

            if 'image/svg' in avatar_url:
                continue

            try:
                file_name = os.path.join(
                    self.avatar_path,
                    f'{self.avatar_name_pattern.findall(avatar_url)[0]}.png'
                )
            except Exception:
                continue

            if os.path.exists(file_name):
                continue

            self.save_avatar(avatar_url, file_name)
            time.sleep(self.delay)

    def save_avatar(self, avatar_url, file_name):
        self.browser.get(avatar_url)
        avatar_name = os.path.basename(file_name)
        with open(file_name, 'wb') as file:
            file.write(
                self.browser.find_element_by_xpath(
                    '//img').screenshot_as_png
            )
        self.logger.info(f"Avatar {avatar_name} done..!")
