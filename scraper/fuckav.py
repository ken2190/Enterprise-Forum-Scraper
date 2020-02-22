import re
import uuid

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)
from scrapy import (
    Request,
    FormRequest
)

REQUEST_DELAY = 0.1
NO_OF_THREADS = 20
USERNAME = "thecreator"
PASSWORD = "Night#Fuck000"
MD5PASSWORD = "2daf343aca1fd2b2075cde2dc60a7129"


class FuckavSpider(SitemapSpider):

    name = "fuckav_spider"

    # Url stuffs
    base_url = "https://fuckav.ru/"

    # Css stuffs
    login_form_css = "form[action*=\"login.php\"]"
    captcha_form_css = "#pagenav_menu + form[action*=\"login.php\"]"

    # Xpath stuffs
    forum_xpath = "//*[not(@class=\"boxcolorbar\")]/a[contains(@href,\"forumdisplay.php?f\")]"
    pagination_xpath = "//a[@class=\"pagination_next\"]/@href"

    thread_xpath = "//tr[@class=\"inline_row\"]"
    thread_first_page_xpath = "//span[contains(@id,\"tid\")]/a/@href"
    thread_last_page_xpath = "//span/span[@class=\"smalltext\"]/a[contains(@href,\"Thread-\")][last()]/@href"
    thread_date_xpath = "//span[@class=\"lastpost smalltext\"]/span[@title]/@title|" \
                        "//span[@class=\"lastpost smalltext\"]/text()[contains(.,\"-\")]"

    thread_pagination_xpath = "//a[@class=\"pagination_previous\"]/@href"
    thread_page_xpath = "//span[@class=\"pagination_current\"]/text()"
    post_date_xpath = "//span[@class=\"post_date postbit_date\"]/text()[contains(.,\"-\")]|" \
                      "//span[@class=\"post_date postbit_date\"]/span[@title]/@title"
    avatar_xpath = "//div[@class=\"author_avatar postbit_avatar\"]/a/img/@src"
    captcha_xpath = "//img[@id=\"imagereg\"]/@src"
    
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
        captcha_token = self.solve_captcha(captcha_url, response)

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
            callback=self.parse_start
        )

    def parse_start(self, response):
        self.logger.info(response.text)


class FuckavScrapper(SiteMapScrapper):
    spider_class = FuckavSpider


if __name__ == "__main__":
    pass
