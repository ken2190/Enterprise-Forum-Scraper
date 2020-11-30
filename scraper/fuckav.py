import re
import uuid

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

REQUEST_DELAY = 0.3
NO_OF_THREADS = 10
USERNAME = "thecreator"
PASSWORD = "Night#Fuck000"
MD5PASSWORD = "2daf343aca1fd2b2075cde2dc60a7129"
USER_ID = ",42737,"


class FuckavSpider(SitemapSpider):

    name = "fuckav_spider"

    # Url stuffs
    base_url = "https://fuckav.ru/"

    # Css stuffs
    login_form_css = "form[action*=\"login.php\"]"
    captcha_form_css = "#pagenav_menu + form[action*=\"login.php\"]"

    # Xpath stuffs
    forum_xpath = "//td[contains(@id,\"f\")]/div/a[contains(@href,\"forumdisplay.php?f\")]/@href|" \
                  "//td[contains(@id,\"f\")]/div/table/tr/td/a[contains(@href,\"forumdisplay.php?f\")]/@href"

    pagination_xpath = "//a[@rel=\"next\"]/@href"

    thread_xpath = "//tbody[contains(@id,\"threadbits_forum\")]/tr"
    thread_first_page_xpath = ".//a[contains(@id,\"thread_title\")]/@href"
    thread_last_page_xpath = ".//span/a[contains(@href,\"showthread\")][font[font]][last()]/@href|" \
                             ".//span[a[font]][last()][following-sibling::span]/a/@href"
    thread_date_xpath = ".//td[contains(@title,\"Ответов\")]/div/text()[1]"

    thread_pagination_xpath = "//a[@rel=\"prev\"]/@href"
    thread_page_xpath = "//span/strong/font/font/text()"
    post_date_xpath = "//a[contains(@name,\"post\")]/following-sibling::text()[1][contains(.,\"-\")]"
    avatar_xpath = "//div[@class=\"smallfont\"]/a/img/@src"
    captcha_xpath = "//img[@id=\"imagereg\"]/@src"

    # Login Failed Message
    login_failed_xpath = '//div[contains(text(), "incorrect username or password")]'

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
    use_proxy = True
    sitemap_datetime_format = "%d-%m-%Y"
    post_datetime_format = "%d-%m-%Y"
    download_delay = REQUEST_DELAY
    concurrent_requests = NO_OF_THREADS

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
            }
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

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
            formcss=self.login_form_css,
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

        # Load captcha
        captcha_url = response.xpath(self.captcha_xpath).extract_first()
        if self.base_url not in captcha_url:
            captcha_url = self.base_url + captcha_url

        # Solve captcha
        captcha_token = self.solve_captcha(
            captcha_url,
            response,
            cookies={
                "User_id": USER_ID,
                "IDstack": quote_plus(USER_ID)
            },
            headers={
                "Referer": "https://fuckav.ru/login.php?do=login",
                "Sec-fetch-dest": "image",
                "Sec-fetch-mode": "no-cors",
                "Sec-fetch-site": "same-origin",
            }
        )

        yield FormRequest.from_response(
            response,
            formcss=self.captcha_form_css,
            formdata={
                "humanverify[input]": captcha_token,
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
        self.crawler.stats.set_value("forum/forum_count", len(all_forums))

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


if __name__ == "__main__":
    pass
