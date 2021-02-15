import os
import re
import time
import logging

from selenium.webdriver import (
    Chrome,
    ChromeOptions,
)
from datetime import (
    datetime,
    timedelta
)
from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper,
    SeleniumSpider
)


USERNAME = "darkcylon"
PASSWORD = "Night#Omerta"
MD5PASS = "8956fb126e264fcf3da8a553e271a0c9"


class OmertaSpider(SeleniumSpider):
    name = 'omerta_spider'
    delay = 0.1

    # Url stuffs
    base_url = "https://omerta.cc/"

    # Css stuffs
    login_form_css = "form[action*=login]"

    # Xpath stuffs
    forum_xpath = "//tr[@align=\"center\"]//a[contains(@href, \"forumdisplay.php?f=\")]/@href"
    pagination_xpath = "//td[@class=\"pagenav_control\"]/a[@rel=\"next\"]/@href"

    thread_xpath = "//tbody[contains(@id,\"threadbits_forum\")]/tr[not(@valign)]"

    thread_first_page_xpath = ".//a[contains(@id,\"thread_title\")]/@href"
    thread_last_page_xpath = ".//td[contains(@id,\"td_threadtitle\")]/div/span[@class=\"smallfont\"]/a[last()]/@href"
    thread_date_xpath = ".//td[not(@nowrap)]/div/span[@class=\"time\"]/preceding-sibling::text()"

    thread_pagination_xpath = "//td[@class=\"pagenav_control\"]/a[@rel=\"prev\"]/@href"
    thread_page_xpath = "//span[contains(@title,\"Showing results\")]/strong/text()"
    post_date_xpath = "//a[contains(@name,\"post\")]/following-sibling::text()[contains(.,\":\")]"

    password_protect_xpath = "//div[@class=\"panel\"]/div/div/p[contains(text(),\"password protected\")]"
    avatar_xpath = "//a[contains(@href,\"member.php?\")]/img/@src"
    # Login Failed Message
    login_failed_xpath = '//div[contains(text(), "an invalid username or password")]'

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

    # Other settings
    use_proxy = "VIP"
    sitemap_datetime_format = "%m-%d-%Y"
    post_datetime_format = "%m-%d-%Y, %I:%M %p"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
            }
        )
        selenium_logger = logging.getLogger("seleniumwire")
        selenium_logger.setLevel(logging.ERROR)
        selenium_logger = logging.getLogger("selenium.webdriver")
        selenium_logger.setLevel(logging.ERROR)
        urllib3_logger = logging.getLogger("urllib3.connectionpool")
        urllib3_logger.setLevel(logging.ERROR)
        self.setup_browser()

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        thread_date = thread_date.strip()

        if "today" in thread_date.lower():
            return datetime.today()
        elif "yesterday" in thread_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        post_date = post_date.strip()

        if "today" in post_date.lower():
            return datetime.today()
        elif "yesterday" in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def setup_browser(self):
        chrome_options = ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={self.headers.get("User-Agent")}')
        prefs = {
            "download.prompt_for_download": False,
            "download.default_directory": self.output_path,
            "savefile.default_directory": self.output_path
        }
        chrome_options.add_experimental_option("prefs", prefs)

        self.browser = Chrome(
            '/usr/local/bin/chromedriver',
            chrome_options=chrome_options)

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            dont_filter=True,
        )

    def parse(self, response):
        self.browser.get(self.base_url)
        time.sleep(self.delay)
        userbox = self.browser.find_element_by_name('vb_login_username')
        passbox = self.browser.find_element_by_name('vb_login_password')
        checkbox = self.browser.find_element_by_name('cookieuser')
        userbox.send_keys(USERNAME)
        passbox.send_keys(PASSWORD)
        checkbox.click()
        submit = self.browser.find_element_by_xpath('//input[@type="submit"]')
        submit.click()
        time.sleep(10)
        super().parse_start()

    # def parse_thread(self, response):

    #     # Synchronize user agent in cloudfare middleware
    #     self.synchronize_headers(response)

    #     # Check if password protected
    #     password_protected = response.xpath(self.password_protect_xpath).extract_first()
    #     if password_protected:
    #         self.logger.info(
    #             "Thread %s has been protected by password. Ignored." % response.url
    #         )
    #         return

    #     # Parse generic thread
    #     yield from super().parse_thread(response)

    #     # Save avatars
    #     avatars = response.xpath("//a[contains(@href,\"member.php?\")]/img")
    #     for avatar in avatars:
    #         avatar_url = avatar.xpath('@src').extract_first()
    #         if self.base_url not in avatar_url:
    #             avatar_url = self.base_url + avatar_url
    #         user_id = avatar.xpath('@alt').re(r'(\w+)\'s')
    #         if not user_id:
    #             continue
    #         file_name = '{}/{}.jpg'.format(self.avatar_path, user_id[0])
    #         if os.path.exists(file_name):
    #             continue
    #         yield Request(
    #             url=avatar_url,
    #             headers=self.headers,
    #             callback=self.parse_avatar,
    #             meta=self.synchronize_meta(
    #                 response,
    #                 default_meta={
    #                     "file_name": file_name,
    #                     "user_id": user_id[0]
    #                 }
    #             )
    #         )

    def parse_avatars(self, response):
        avatars = response.xpath("//a[contains(@href,\"member.php?\")]/img")
        for avatar in avatars:
            avatar_url = avatar.xpath('@src')[0]
            if self.base_url not in avatar_url:
                avatar_url = self.base_url + avatar_url
            alts = avatar.xpath('@alt')
            user_id = re.search(r'(\w+)\'s', alts[0])
            if not user_id:
                continue
            file_name = '{}/{}.jpg'.format(self.avatar_path, user_id[0].strip("'s"))
            if os.path.exists(file_name):
                continue

            self.save_avatar(avatar_url, file_name)
            time.sleep(self.delay)


class OmertaScrapper(SiteMapScrapper):

    spider_class = OmertaSpider
    site_name = 'omerta.cc'
    site_type = 'forum'


if __name__ == "__main__":
    pass
