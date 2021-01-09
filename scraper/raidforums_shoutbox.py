import os
import re
import logging
import time
import dateparser

from selenium.webdriver.firefox.options import Options
from scrapy import Request
from selenium.webdriver import (
    Chrome,
    ChromeOptions,
)
from scraper.base_scrapper import (
    SeleniumSpider,
    SiteMapScrapper
)

from scrapy.exceptions import CloseSpider

from lxml.html import fromstring


REQUEST_DELAY = 3

USERNAME = "gordon418"
PASSWORD = "Readytogo418"

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'

class RaidforumsShoutboxSpider(SeleniumSpider):

    name = 'raidforums_shoutbox'
    delay = REQUEST_DELAY

    # Url stuffs
    base_url = "https://raidforums.com/"
    login_url = f'{base_url}/member.php?action=login'

    hcaptcha_site_key_xpath = "//div[@data-sitekey]/@data-sitekey"


    # Other settings
    use_proxy = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )
        # Init logger
        selenium_logger = logging.getLogger("seleniumwire")
        selenium_logger.setLevel(logging.ERROR)
        selenium_logger = logging.getLogger("selenium.webdriver")
        selenium_logger.setLevel(logging.ERROR)
        urllib3_logger = logging.getLogger("urllib3.connectionpool")
        urllib3_logger.setLevel(logging.ERROR)
        self.setup_browser()

    def setup_browser(self):
        chrome_options = ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
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
            url=self.login_url,
            headers=self.headers,
            dont_filter=True,
            # meta={'proxy': PROXY}
        )

    def parse(self, response):
        self.browser.get(self.login_url)
        time.sleep(self.delay)
        userbox = self.browser.find_element_by_name('username')
        passbox = self.browser.find_element_by_name('password')
        userbox.send_keys(USERNAME)
        passbox.send_keys(PASSWORD)
        submit = self.browser.find_element_by_xpath('//input[@type="submit"]')
        submit.click()
        time.sleep(10)

        # Solve hcaptcha
        response = fromstring(self.browser.page_source)
        site_url = self.browser.current_url
        site_key = response.xpath(self.hcaptcha_site_key_xpath)[0]
        captcha_response = self.solve_hcaptcha(response, site_url=site_url, site_key=site_key, user_agent=USER_AGENT)
        if captcha_response:
            self.logger.info(f'Captcha Solved: {captcha_response}')
        else:
            self.logger.info(f'Captcha Solve Failed')
            return

        # Display captcha box
        self.browser.execute_script(
            "document.querySelector(\"[name=h-captcha-response]\").setAttribute(\"style\",\"display: block\")"
        )
        self.browser.execute_script(
            "document.querySelector(\"[name=g-recaptcha-response]\").setAttribute(\"style\",\"display: block\")"
        )

        # Input captcha response
        self.browser.execute_script(
            "document.querySelector(\"[name=h-captcha-response]\").innerText = \"%s\"" % captcha_response
        )
        self.browser.execute_script(
            "document.querySelector(\"[name=g-recaptcha-response]\").innerText = \"%s\"" % captcha_response
        )

        # Submit form
        self.browser.execute_script(
            "document.querySelector(\"[type=submit]\").click()"
        )
        time.sleep(10)
        self.parse_shoutbox()

    def parse_shoutbox(self):
        archive_button = self.browser.find_element_by_xpath('//a[@id="log"]')
        archive_button.click()

        time.sleep(5)
        el_page_count = self.browser.find_element_by_id('pagecount')
        page_count = el_page_count.get_attribute("data-pagemax")

        for i in range(0, int(page_count)):
            try:
                el_generate_html = self.browser.find_element_by_xpath('//button[@id="htmlgenerator"]')
                el_generate_html.click()

                self.logger.info(f'Page {i+1} Done')

                el_next_page = self.browser.find_element_by_xpath('//button[@id="page_next"]')
                el_next_page.click()
                
                time.sleep(1)
            except:
                continue
        self.browser.quit()


class RaidforumsShoutboxScrapper(SiteMapScrapper):

    spider_class = RaidforumsShoutboxSpider
    site_name = 'raidforums_shoutbox'
    site_type = 'forum'
