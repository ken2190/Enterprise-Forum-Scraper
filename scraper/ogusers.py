import os
import re
import sys
import uuid

from scrapy import Request, FormRequest
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

# USER = 'Exabyte'
# PASS = 'OG-new!pass'
USER = 'sgqrpysbnt'
PASS = 'Y8Kdh86Q2TancWz'
REQUEST_DELAY = .6
NO_OF_THREADS = 16


class OgUsersSpider(SitemapSpider):

    name = 'ogusers_spider'

    # Url stuffs
    base_url = "https://ogusers.com/"
    login_url = "https://ogusers.com/member.php?action=login"

    # Css stuffs
    login_form_xpath = "//form[@action='member.php']"
    forum_xpath = "//a[contains(@href, 'Forum-')]/@href"

    # Xpath stuffs
    pagination_xpath = "//a[@class='pagination_next']/@href"

    thread_xpath = "//tr[contains(@class, 'thread_row')]"

    thread_first_page_xpath = "//span[contains(@class,'subject')]/a[contains(@href,'Thread-')]/@href"

    thread_last_page_xpath = "//tr[contains(@class, 'thread_row')]//td[2]//a/@href"

    thread_date_xpath = "//span[contains(@class,'lastpost')]/a/span/@title|"\
                        "//span[contains(@class,'lastpost')]/a/text()"

    thread_pagination_xpath = "//a[@class='pagination_previous']/@href"

    thread_page_xpath = "//span[contains(@class,'pagination_current')]/text()"

    post_date_xpath = "//div//div[contains(@class,'pb_date')]/text()"

    avatar_xpath = "//td[1]//a/img/@src|//img[@class='profileshow']/@src"

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*avatar_(\d+\.\w+)\?",
        re.IGNORECASE
    )

    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )

    get_users = '--getusers' in sys.argv

    #captcha stuffs
    bypass_success_xpath = '//a[@class="guestnav" and text()="Login"]'

    # Other settings
    use_proxy = True
    sitemap_datetime_format = "%m-%d-%Y"
    handle_httpstatus_list = [403]
    get_cookies_retry = 10
    fraudulent_threshold = 10

    def get_avatar_file(self, url):

        if "image/svg" in url:
            return

        return super().get_avatar_file(url)

    def start_requests(self):
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
            url=self.login_url,
            headers=self.headers,
            meta=meta,
            cookies=cookies,
            callback=self.parse_login
        )

    def parse_login(self, response):
        # Synchronize user agent in cloudfare middleware
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response,
            formxpath=self.login_form_xpath,
            formdata={
                "username": USER,
                "password": PASS
            },
            headers=self.headers,
            dont_filter=True,
            # callback=self.parse_start,
            meta=self.synchronize_meta(response)
        )

    def parse_thread(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Load topic_id
        topic_id = response.meta.get("topic_id")

        # Check current page to scrape from last page
        current_page = response.xpath(self.thread_page_xpath).extract_first()
        last_page = response.xpath(self.thread_last_page_xpath).extract_first()
        if current_page == "1" and last_page:

            if self.base_url not in last_page:
                last_page = self.base_url + last_page

            yield Request(
                url=last_page,
                headers=self.headers,
                callback=super().parse_thread,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "topic_id": topic_id
                    }
                )
            )

        # Parse main thread
        yield from super().parse_thread(response)

        # Parse avatar thread
        yield from super().parse_avatars(response)


        if self.get_users:

            # Save user content
            users = response.xpath("//div[@class=\"postbitdetail\"]/span/a")
            for user in users:
                user_url = user.xpath("@href").extract_first()
                if self.base_url not in user_url:
                    user_url = self.base_url + user_url
                user_name = user.xpath("span/text()").extract_first()
                if not user_name:
                    user_name = user.xpath("text()").extract_first()
                if not user_name:
                    user_name = user.xpath("font/text()").extract_first()
                file_name = '{}/{}.html'.format(self.user_path, user_name)
                if os.path.exists(file_name):
                    continue
                yield Request(
                    url=user_url,
                    headers=self.headers,
                    callback=self.parse_user,
                    meta=self.synchronize_meta(
                        response,
                        default_meta={
                            "file_name": file_name,
                            "user_name": user_name,
                        }
                    )
                )

    def parse_user(self, response):
        # Synchronize headers
        self.synchronize_headers(response)

        # Save user contents
        file_name = response.meta.get("file_name")
        user_name = response.meta.get("user_name")
        with open(file_name, 'wb+') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(
                f"User {user_name} done..!"
            )

        user_history = response.xpath(
            "//div[@class=\"usernamehistory\"]/a"
        )

        # Parse user history
        if user_history:
            history_url = user_history.xpath("@href").extract_first()

            if self.base_url not in history_url:
                history_url = self.base_url + history_url

            yield Request(
                url=history_url,
                headers=self.headers,
                callback=self.parse_user_history,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "user_name": user_name,
                    }
                )
            )

    def parse_user_history(self, response):
        user_name = response.meta['user_name']
        file_name = '{}/{}-history.html'.format(self.user_path, user_name)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(
                f"History for user {user_name} done..!"
            )

    def get_cookies_extra(self, browser):
        def find_element(name):
            for element in browser.find_elements_by_name(name):
                if element.is_displayed():
                    return element

        try:
            find_element('username').send_keys(USER)
            password_field = find_element('password')
            password_field.send_keys(PASS)
            password_field.submit()
        except:
            return False

        # Check if login success
        return USER.lower() in browser.page_source.lower()


class OgUsersScrapper(SiteMapScrapper):

    spider_class = OgUsersSpider
    site_name = 'ogusers.com'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "DOWNLOAD_DELAY": REQUEST_DELAY,
                "CONCURRENT_REQUESTS": NO_OF_THREADS,
                "CONCURRENT_REQUESTS_PER_DOMAIN": NO_OF_THREADS,
            }
        )
        return settings
