import re
import base64

from scrapy import Request, FormRequest
from scrapy.exceptions import CloseSpider
from unicaps import CaptchaSolver, CaptchaSolvingService
from unicaps.common import CaptchaCharType, CaptchaAlphabet
from unicaps.exceptions import SolutionWaitTimeout, UnableToSolveError, UnicapsException

from scraper.base_scrapper import (
    MarketPlaceSpider,
    SiteMapScrapper
)

REQUEST_DELAY = 0.5
NO_OF_THREADS = 5
MAX_TRY_TO_LOG_IN_COUNT = 3

USERNAME = "blastedone"
PASSWORD = "Chq#Blast888"

PROXY = 'http://127.0.0.1:8118'


class DarkBaySpider(MarketPlaceSpider):

    name = "darkbay_spider"

    # Url stuffs
    base_url = None
    base_urls = [
        "http://darkbayupenqdqvv.onion/",
        "http://limegr336ldbnpzu.onion/",
        "http://agrzq76nwjxwvrzc.onion/",
        "http://ba3ozrpprih6vd3m.onion/",
        "http://xzzl6zjwrhnmzhkf.onion/",
        "http://oh33m3pka6lvc2sb.onion/",
        "http://bfc3czua5idp5d5y.onion/",
        "http://zwcgtqtdviw7gkbn.onion/"
    ]

    # xpath stuffs
    login_form_xpath = '//form[contains(@action, "/signin")]'
    captcha_url_xpath = f'{login_form_xpath}//img/@src'
    market_url_xpath = ('//div[@class="list-group categories" or '
                       '@class="pl-3 subcategories"]/details/a/@href')
    product_url_xpath = '//a[contains(@href, "/product/")]/@href'
    next_page_xpath = '//a[@rel="next"]/@href'
    user_xpath = '//a[contains(@href, "/vendor/")]/@href'
    avatar_xpath = '//img[contains(@class, "image-responsive")]/@src'
    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    use_proxy = False
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    _base_url_index = 0
    _try_to_log_in_count = 0

    def start_requests(self):
        self.base_url = self.base_urls[self._base_url_index]
        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse_login,
            errback=self.rotate_base_url,
            dont_filter=True,
            meta={'proxy': PROXY}
        )

    def rotate_base_url(self, failure):
        self._base_url_index += 1

        if self._base_url_index >= len(self.base_urls):
            raise CloseSpider(reason='site_is_down')

        yield from self.start_requests()

    def parse_login(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        self._try_to_log_in_count += 1

        # solve CAPTCHA
        try:
            solved_captcha = self.solve_captcha(response)
        except (SolutionWaitTimeout, UnableToSolveError):
            if self._try_to_log_in_count >= MAX_TRY_TO_LOG_IN_COUNT:
                raise CloseSpider(reason='access_is_blocked')
            yield from self.start_requests()
            return
        except UnicapsException as exc:
            self.logger.error('Unable to solve the CAPTCHA: %s', exc)
            raise CloseSpider(reason='access_is_blocked')

        captcha_text = str(solved_captcha.solution).lower()
        self.logger.info(
            "Captcha has been solved: %s" % captcha_text
        )

        formdata = {
            'username': USERNAME,
            'password': PASSWORD,
            "captcha": captcha_text
        }

        yield FormRequest.from_response(
            response=response,
            formxpath=self.login_form_xpath,
            formdata=formdata,
            headers=self.headers,
            dont_filter=True,
            meta=self.synchronize_meta(response),
            callback=self.check_if_logged_in,
            cb_kwargs=dict(solved_captcha=solved_captcha)
        )

    def check_if_logged_in(self, response, solved_captcha):
        if response.xpath(self.market_url_xpath):
            solved_captcha.report_good()
            yield from self.parse_start(response)
        elif response.xpath('//p[@class="text-danger" and text()="Invalid Captcha"]'):
            solved_captcha.report_bad()
            if self._try_to_log_in_count >= MAX_TRY_TO_LOG_IN_COUNT:
                raise CloseSpider(reason='access_is_blocked')
            yield from self.start_requests()
            return
        else:
            err_msg = response.xpath('//p[@class="text-danger"]/text()').get()
            err_msg = err_msg or 'Unknown error'
            self.logger.error(err_msg)
            raise CloseSpider(reason='access_is_blocked')

    def solve_captcha(self, response):
        captcha_url = response.xpath(self.captcha_url_xpath).get()
        captcha_data = base64.b64decode(captcha_url.split(',', 1)[1])

        solver = CaptchaSolver(
            CaptchaSolvingService.ANTI_CAPTCHA,
            self.captcha_token
        )

        return solver.solve_image_captcha(
            image=captcha_data,
            char_type=CaptchaCharType.ALPHANUMERIC,
            is_phrase=False,
            is_case_sensitive=False,
            is_math=False,
            alphabet=CaptchaAlphabet.LATIN
        )

    def get_user_id(self, url):
        return url.rsplit('vendor/', 1)[-1]

    def get_file_id(self, url):
        return url.rsplit('product/', 1)[-1]


class DarkbayScrapper(SiteMapScrapper):
    spider_class = DarkBaySpider
    site_name = 'darkbay (darkbayupenqdqvv.onion)'

    def __init__(self, kwargs):
        kwargs['get_users'] = True
        super().__init__(kwargs)
