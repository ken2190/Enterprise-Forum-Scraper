import re
import scrapy
import logging


from seleniumwire.webdriver import (
    Chrome,
    ChromeOptions,
)
from scrapy import (
    Request,
    FormRequest
)
from datetime import (
    datetime, timedelta
    )

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


USERNAME = "Doz3r"
PASSWORD = "DOCPVfmd"
PASSWORD_HASH = "70322e243f1c161437160d1e0a46413629260311330e41181e741c1f25707f3e"


class JstashBazarSpider(SitemapSpider):

    name = 'jstash_bazar_spider'

    # Url stuffs
    base_url = "http://jstash.bazar"
    login_url = "/login"

    # Css stuffs
    captcha_url_css = ".in>p>img::attr(src)"
    raw_pre_cookies_css = "#cafo::attr(onsubmit)"
    bypass_captcha_form_css = "#cafo"
    login_form_css = "._form.login"
    login_captcha_url_css = "img._captcha::attr(src)"
    captcha_instruction_css = "#captcha::attr(placeholder)"
    logout_button_css = "#transfers + td>a[href=\"/logout\"]"

    # Other settings
    handle_httpstatus_list = [511]
    sitemap_datetime_format = '%d.%m.%Y'
    post_datetime_format = '%d.%m.%Y, %H:%M'
    use_proxy = 'On'
    
    # Regex stuffs
    topic_pattern = re.compile(
        r".*t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r"&page=(\d+)",
        re.IGNORECASE
    )
    get_pre_cookies = re.compile(
        "(?<=\')ht\=.*?(?=\')",
        re.IGNORECASE
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "http://" + self.get_blockchain_domain(self.base_url)
        self.login_url = self.base_url + self.login_url

    def parse(self, response):
        # Load captcha url
        captcha_url = response.css(self.captcha_url_css).extract_first()
        
        # Handle captcha image content
        image_content = captcha_url.replace("data:image/gif;base64,", "")
        
        # Solve captcha
        captcha = self.solve_captcha(
            image_content,
            response
        )
        self.logger.info(
            "Captcha has been solved: %s" % captcha
        )

        # Load raw pre cookies
        pre_cookies = self.get_pre_cookies.search(
            response.css(self.raw_pre_cookies_css).extract_first()
        ).group()

        # Load bypass cookies
        cookies = self.load_cookies(
            pre_cookies + captcha.upper()
        )

        yield from self.parse_login(cookies)

    def parse_login(self, cookies):

        # Load login cookies
        login_cookies = self.get_login_cookies(cookies)
        self.logger.info(
            "Login cookies: %s" % login_cookies
        )

        yield Request(
            url=self.base_url,
            dont_filter=True,
            headers=self.headers,
            cookies=login_cookies,
            callback=self.parse_start,
            meta={
                "cookies": cookies
            }
        )

    def get_login_cookies(self, cookies, proxy=False, fraud_check=False):

        # Convert cookies
        cookiejar = []
        for name, value in cookies.items():
            cookiejar.append(
                {"name": name, "value": value}
            )

        # Init logger
        selenium_logger = logging.getLogger("seleniumwire")
        selenium_logger.setLevel(logging.ERROR)

        # Init options
        options = ChromeOptions()
        # options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument(f'user-agent={self.headers.get("User-Agent")}')

        # Init web driver arguments
        webdriver_kwargs = {
            "executable_path": "/usr/local/bin/chromedriver",
            "options": options
        }

        # Fraud check
        ip = None
        if fraud_check:
            ip = self.ip_handler.get_good_ip()

        # Init proxy
        if proxy:
            if ip is None:
                proxy = PROXY % (
                    "%s-session-%s" % (
                        PROXY_USERNAME,
                        uuid.uuid1().hex
                    ),
                    PROXY_PASSWORD
                )
            else:
                proxy = PROXY % (
                    "%s-ip-%s" % (
                        PROXY_USERNAME,
                        ip
                    ),
                    PROXY_PASSWORD
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

        # Load login page
        browser.get(self.login_url)

        # Set cookies
        for item in cookiejar:
            browser.add_cookie(item)

        # Reload login page
        browser.get(self.login_url)

        # Send username
        username_button = browser.find_element_by_css_selector(
            "#login"
        )
        username_button.send_keys(USERNAME)

        # Send password
        password_button = browser.find_element_by_css_selector(
            "#password"
        )
        password_button.send_keys(PASSWORD)

        # Load captcha image
        captcha_image = browser.find_element_by_css_selector(
            "img._captcha"
        )
        captcha_content = captcha_image.get_attribute("src").replace(
            "data:image/gif;base64,", 
            ""
        )

        # Load captcha instruction
        instruction_button = browser.find_element_by_css_selector(
            "#captcha"
        )
        self.captcha_instruction = instruction_button.get_attribute("placeholder")
        self.logger.info(
            "Captcha instruction: %s" % self.captcha_instruction
        )

        # Solve captcha
        captcha = self.solve_captcha(
            captcha_content,
            None
        )
        self.logger.info(
            "Captcha has been solved: %s" % captcha
        )

        # Input captcha
        captcha_button = browser.find_element_by_css_selector(
            "#captcha"
        )
        captcha_button.send_keys(captcha)

        # Login button
        login_button = browser.find_element_by_css_selector(
            "button[type=submit]"
        )
        login_button.click()

        # Load cookies
        cookies = browser.get_cookies()

        # Report cookies and ip
        login_cookies = {
            c.get("name"): c.get("value") for c in cookies
        }

        # Close browser
        browser.quit()

        return login_cookies

    def parse_start(self, response):
        # Check logout button
        logout_button = response.css(self.logout_button_css).extract_first()
        if not logout_button:
            yield from self.parse_login(response.meta.get("cookies"))
            return
        
        self.logger.info(response.text)

    

class JstashBazarScrapper(SiteMapScrapper):

    spider_class = JstashBazarSpider
    site_name = 'jstash.bazar'
    site_type = 'forum'
