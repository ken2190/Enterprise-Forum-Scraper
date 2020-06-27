import os
import re
import uuid
import json
import dateparser

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

USERNAME = "heisenberg404"
PASSWORD = "helloworld"

class BHFIOSpider(SitemapSpider):

    name = 'bhfio_spider'

    # Url stuffs
    base_url = 'https://bhf.io'
    login_url = 'https://bhf.io/login/login'
    start_urls = ["https://bhf.io/"]

    # Regex stuffs
    topic_pattern = re.compile(r'threads/(\d+)')
    avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
    pagination_pattern = re.compile(r'.*page-(\d+)')

    # Css stuffs
    login_form_css = "form[action]"
    backup_code_url = f'{base_url}/login/two-step?provider=backup&remember=1&'\
                      f'_xfRedirect={base_url}/'
    account_css = r'a[href="/account/"]'

    # Xpath stuffs
    forum_xpath = "//a[contains(@href,\"/forums\")]/@href"
    pagination_xpath = "//a[contains(@class,\"pageNav-jump--next\")]/@href"
    thread_xpath = "//div[contains(@class,\"structItem--thread\")]"
    thread_first_page_xpath = "//div[@class=\"structItem-title\"]/a/@href"
    thread_last_page_xpath = "//span[@class=\"structItem-pageJump\"]/"\
                             "a[last()]/@href"
    thread_date_xpath = "//time[contains(@class,\"structItem-latestDate\")]"\
                        "/@title"
    thread_pagination_xpath = "//a[contains(@class,\"pageNav-jump--prev\")]"\
                              "/@href"
    thread_page_xpath = "//li[contains(@class,\"pageNav-page--current\")]"\
                        "/a/text()"
    post_date_xpath = "//div[@class=\"message-attribution-main\"]"\
                      "/a[@class=\"u-concealed\"]/time/@title"

    avatar_xpath = "//img[contains(@class,\"avatar\")]/@src"

    # Other settings
    use_proxy = False
    sitemap_datetime_format = "%b %d, %Y at %I:%M %p"
    post_datetime_format = "%b %d, %Y at %I:%M %p"
    download_delay = 0.3
    download_thread = 10

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Update headers
        self.headers.update(
            {
                'referer': 'https://bhf.io/',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/83.0.4103.106 Safari/537.36',
            }
        )

        # Load backup codes
        self.backup_code_file = os.path.join(
            os.getcwd(),
            "code/%s" % self.name
        )
        with open(
            file=self.backup_code_file,
            mode="r",
            encoding="utf-8"
        ) as file:
            self.backup_codes = [
                re.sub(r'\s+', '', code) for code in file.read().split("\n")
            ]

    def parse_thread_date(self, thread_date):
        if not thread_date:
            return
        return dateparser.parse(thread_date.strip())

    def parse_post_date(self, post_date):
        if not post_date:
            return
        return dateparser.parse(post_date.strip())

    def write_backup_codes(self):
        with open(
            file=self.backup_code_file,
            mode="w+",
            encoding="utf-8"
        ) as file:
            file.write(
                "\n".join(self.backup_codes)
            )

    def start_requests(self):
        yield Request(
            url=self.login_url,
            dont_filter=True,
            headers=self.headers,
            callback=self.parse_login,
            meta={
                "cookiejar": uuid.uuid1().hex
            }
        )

    def parse_login(self, response):
        self.synchronize_headers(response)
        token = response.xpath(
            '//input[@name="_xfToken"]/@value').extract_first()
        params = {
            'login': USERNAME,
            'password': PASSWORD,
            "remember": '1',
            '_xfRedirect': self.base_url,
            '_xfToken': token
        }
        self.logger.info(f'Login Token is: {token}')
        yield FormRequest(
            url=self.login_url,
            callback=self.parse_post_login,
            formdata=params,
            headers=self.headers,
            dont_filter=True,

        )

    def parse_post_login(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)
        # Load backup code url
        yield Request(
            url=self.backup_code_url,
            headers=self.headers,
            dont_filter=True,
            callback=self.parse_backup_code,
        )

    def parse_backup_code(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)
        if response.url == f'{self.base_url}/':
            yield from self.parse(response)
            return

        # Load backup code
        code = self.backup_codes[0]
        self.backup_codes = self.backup_codes[1:]
        token = response.xpath(
            '//input[@name="_xfToken"]/@value').extract_first()
        self.headers.update({
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'en-US,en;q=0.9,hi;q=0.8,ru;q=0.7',
            'origin': 'https://bhf.io',
            'referer': self.backup_code_url,
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'x-requested-with': 'XMLHttpRequest',
        })
        self.logger.info(f'Code is: {code}')
        self.logger.info(f'Two-step Token is: {token}')
        params = {
            'code': code,
            'trust': '1',
            'trust_permanent': '1',
            'confirm': '1',
            'provider': 'backup',
            'remember': '1',
            '_xfRedirect': f'{self.base_url}/',
            '_xfToken': token,
            '_xfRequestUri': '/login/two-step?provider=backup&remember=1&'
                             '_xfRedirect=https://bhf.io/',
            '_xfWithData': '1',
            '_xfToken': token,
            '_xfResponseType': 'json',
        }
        yield FormRequest(
            url='https://bhf.io/login/two-step',
            callback=self.parse_post_backup_code,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
            meta={'code': code}
        )

    def parse_post_backup_code(self, response):

        code = response.meta.get("code")
        self.synchronize_headers(response)

        json_data = json.loads(response.text)
        if json_data.get('status') == 'ok':
            self.logger.info("Code %s success." % code)
            yield Request(
                url=self.base_url,
                headers=self.headers,
                dont_filter=True,
                callback=self.parse,
            )
            self.write_backup_codes()
            return

        # If not account and no more backup codes, return
        if not self.backup_codes:
            self.logger.info(
                "None of backup code work."
            )
            self.write_backup_codes()
            return

        # If not account, try other code
        self.logger.info(
            "Code %s failed." % code
        )
        yield Request(
            url=self.backup_code_url,
            headers=self.headers,
            dont_filter=True,
            callback=self.parse_backup_code,
            meta=self.synchronize_meta(response)
        )
        return

    def get_topic_id(self, url=None):
        topic_id = self.topic_pattern.findall(url)
        try:
            return topic_id[0]
        except Exception:
            return

    def parse_thread_url(self, thread_url):
        return thread_url.replace(".vc", ".io")

    def parse(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:
            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            # if 'forums/161/' not in forum_url:
            #     continue
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class BHFIOScrapper(SiteMapScrapper):

    spider_class = BHFIOSpider
    request_delay = 0.8
    no_of_threads = 4
    site_name = 'bhf.io'

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': self.request_delay,
                'CONCURRENT_REQUESTS': self.no_of_threads,
                'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads
            }
        )
        return spider_settings
