import re
import uuid
import hashlib
import time

from urllib.parse import quote_plus

from datetime import (
    datetime,
    timedelta
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)
from scrapy import (
    Request,
    FormRequest
)

USERNAME = "Kaddafi"
PASSWORD = "AVS3rg910_1"
MD5PASSWORD = hashlib.md5(PASSWORD.encode('utf-8')).hexdigest()
USER_ID = ",42737,"

MIN_DELAY = 1
MAX_DELAY = 3

PROXY = 'http://127.0.0.1:8118'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36'


class FuckavSpider(SitemapSpider):
    name = "fuckav_spider"

    # Url stuffs
    base_url = "https://fuckav.ru/"

    # Css stuffs
    login_form_css = captcha_form_css = '//form[@method="post"]'
    
    # Xpath stuffs
    forum_xpath = "//td[contains(@id,'f')]/div/a[contains(@href,'forumdisplay.php?f')]/@href|" \
                  "//td[contains(@id,'f')]/div/table/tr/td/a[contains(@href,'forumdisplay.php?f')]/@href"

    pagination_xpath = "//a[@rel='next']/@href"

    thread_xpath = "//tbody[contains(@id,'threadbits_forum')]/tr[contains(., 'от')]"
    thread_first_page_xpath = ".//a[contains(@id,'thread_title_')]/@href"
    thread_last_page_xpath = ".//span[@class='smallfont']/a[contains(@href,'showthread')][last()]/@href"
    thread_date_xpath = ".//td[contains(@title,'Ответов')]/div/text()[1]"

    sitemap_datetime_format = "%d-%m-%Y"
    post_datetime_format = "%d-%m-%Y"

    thread_pagination_xpath = "//a[@rel='prev']/@href"
    thread_page_xpath = "//span/strong/font/font/text()"
    post_date_xpath = "//a[contains(@name,'post')]/following-sibling::text()[1][contains(.,'-')]"
    avatar_xpath = "//div[@class='smallfont']/a/img/@src"
    captcha_xpath = "//img[@id='imagereg']/@src"

    # Login Failed Message
    login_failed_xpath = '//div[contains(., "Вы ввели неправильное имя или пароль")] |' \
                         '//input[@name="vb_login_username"]'
    captcha_failed_xpath = '//div[contains(@class, "alert alert-danger") and contains(., "The Captcha code")]'

    # Regex stuffs
    topic_pattern = re.compile(
        r"t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )
    get_session_hash = re.compile(
        r"(?<=sessionhash\=).*?(?=\"\;)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "On"
    session_hash = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )

    def parse_thread_date(self, thread_date):
        # Standardize thread date
        thread_date = thread_date.strip().lower()

        if "минут" in thread_date:
            return datetime.today()
        if "час" in thread_date:
            return datetime.today()
        elif "день" in thread_date:
            day_offset = int(thread_date.split()[0])
            return datetime.today() - timedelta(days=day_offset)
        elif "недель" in thread_date:
            day_offset = int(thread_date.split()[0]) * 7
            return datetime.today() - timedelta(days=day_offset)
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        # Standardize post date
        post_date = post_date.strip().lower()

        try:
            return datetime.strptime(
                post_date[-10:],
                self.post_datetime_format
            )
        except Exception as err:
            return datetime.strptime(
                post_date[:10],
                self.post_datetime_format
            )

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                "cookiejar": uuid.uuid1().hex
            },
            errback=self.check_site_error,
            dont_filter=True
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        time.sleep(2)

        # Load session hash
        session_hash = self.get_session_hash.search(
            response.text
        ).group()

        yield Request(
            url=self.base_url,
            headers=self.headers,
            dont_filter=True,
            meta=self.synchronize_meta(response),
            cookies={
                "sessionhash": session_hash
            },
            callback=self.parse_login
        )

    def parse_login(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response,
            formxpath=self.login_form_css,
            formdata={
                "vb_login_username": USERNAME,
                "vb_login_password": "",
                "s": "",
                "securitytoken": "guest",
                "do": "login",
                "vb_login_md5password": MD5PASSWORD,
                "vb_login_md5password_utf": MD5PASSWORD
            },
            dont_filter=True,
            meta=self.synchronize_meta(response),
            callback=self.parse_captcha
        )

    def parse_captcha(self, response):

        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        USER_ID = response.xpath("//div[@id='userdata_el']/@user_id")
        # Load captcha
        captcha_url = response.xpath(self.captcha_xpath).extract_first()
        if self.base_url not in captcha_url:
            captcha_url = self.base_url + captcha_url

        # Solve captcha
        captcha_token = self.solve_captcha(
            captcha_url,
            response,
            cookies={
                "sessionhash": self.session_hash,
                # "IDstack": quote_plus(USER_ID)
            },
            headers={
                "Referer": "https://fuckav.ru/login.php?do=login",
                "Sec-fetch-dest": "image",
                "Sec-fetch-mode": "no-cors",
                "Sec-fetch-site": "same-origin",
            }
        )

        if not captcha_token:
            yield from self.start_requests()
        else:
            print(f"Captcha Token: {captcha_token}")
            yield FormRequest.from_response(
                response,
                formxpath=self.captcha_form_css,
                formdata={
                    "humanverify[input]": captcha_token,
                    "humanverify[hash]": response.xpath("//input[@id='hash']/@value").extract()[0],
                    "s": "",
                    "securitytoken": "guest",
                    "do": "dologin",
                    "vb_login_password": MD5PASSWORD,
                    "vb_login_username": USERNAME,
                    "url": "https://fuckav.ru/index.php",
                    "cookieuser": "0",
                    "postvars": "",
                    "logintype": ""
                },
                headers=self.headers,
                meta=self.synchronize_meta(response),
                callback=self.parse_redirect
            )

    def parse_redirect(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse_start,
            dont_filter=True,
            meta=self.synchronize_meta(response),
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        # Check if login failed
        self.check_if_logged_in(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", len(all_forums))

        # Loop forum
        for forum_url in all_forums:
            # Standardize forum url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url

            yield Request(
                url=forum_url,
                headers=self.headers,
                meta=self.synchronize_meta(response),
                callback=self.parse_forum
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatars
        yield from super().parse_avatars(response)


class FuckavScrapper(SiteMapScrapper):
    spider_class = FuckavSpider
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "AUTOTHROTTLE_ENABLED": True,
                "AUTOTHROTTLE_START_DELAY": MIN_DELAY,
                "AUTOTHROTTLE_MAX_DELAY": MAX_DELAY
            }
        )
        return settings


if __name__ == "__main__":
    pass
