import re
from scraper.base_scrapper import (
    MarketPlaceSpider,
    SiteMapScrapper
)
from scrapy import Request, FormRequest

PROXY = 'http://127.0.0.1:8118'

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0"

USER = 'Cyrax22'
PASS = 'S5eVZWqf!3wNdtb'

# recovery key: Your recovery key is HCjrcs23snxjRVR8kpR1c1J6wj2GHDUojQpRJ33OcH1AYMNQ3MVVBG3r5zSeftmaj4mFgGV3WKks6z85mvpprOs1XCtan5qxkta2h70mqxu3FJ47RxofBYegANeZoAsO


class SilkRoad4Spider(MarketPlaceSpider):

    name = "silkroad4_spider"

    # Url stuffs
    login_url = base_url = "http://silkroadxjzvoyxh.onion/"

    # xpath stuffs
    login_form_xpath = captcha_form_xpath = '//form[@method="POST"]'
    lonin_user_xpath = "//input[@name='username']"
    captcha_url_xpath = '//img[contains(@src, "captchas")]/@src'
    market_url_xpath = '//a[contains(@href,"cat=")]/@href'
    product_url_xpath = '//a[contains(@href, "?listing=")]/@href'
    next_page_xpath = '//input[@value="Next Page"]'\
                      '/preceding-sibling::input[@name="reqpage"][1]/@value'
    user_xpath = '//a[contains(text(), "View Listings")]'\
                 '/following-sibling::a[contains(@href, "profile=")][1]/@href'
    avatar_xpath = '//div[@id="img"]/img/@src'
    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    use_proxy = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )

    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip"]
            if response.meta.get(key)
        }

        meta.update(default_meta)
        meta.update({'proxy': PROXY})

        return meta

    def get_product_next_page(self, response):
        match = re.findall(r'cat=(\d+)', response.url)
        if not match:
            return
        next_page_number = response.xpath(self.next_page_xpath).extract_first()
        if next_page_number:
            return f'{self.base_url}?road=&reqpage={next_page_number}'\
                   f'&cat={match[0]}'
        return

    def get_user_id(self, url):
        return url.rsplit('profile=', 1)[-1]

    def get_file_id(self, url):
        return url.rsplit('listing=', 1)[-1]

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse_login,
            dont_filter=True,
            meta={
                'proxy': PROXY,
            }
        )

    def parse_login(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # check 1st level of captcha
        if 'you must complete a captcha' in response.text:
            url = response.urljoin('auth.php')
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_first_captcha,
                dont_filter=True,
                meta=self.synchronize_meta(response)
            )
        else:
            yield from self.parse_captcha(response)

    def parse_first_captcha(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load captcha url
        captcha_url = response.xpath(
            self.captcha_url_xpath).extract_first()
        captcha_url = response.urljoin(captcha_url)
        captcha = self.solve_captcha(
            captcha_url,
            response
        )
        self.logger.info(
            "Captcha has been solved: %s" % captcha
        )
        auth_url = response.urljoin(f'auth.php?a={captcha}')

        yield Request(
            url=auth_url,
            headers=self.headers,
            callback=self.parse_captcha,
            dont_filter=True,
            meta=self.synchronize_meta(response)
        )

    def parse_captcha(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)
        
        if not response.xpath(self.lonin_user_xpath).extract_first():
            url = response.urljoin('auth.php')
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_first_captcha,
                dont_filter=True,
                meta=self.synchronize_meta(response)
            )
        else:
            # Load cookies
            cookies = response.request.headers.get("Cookie", '').decode("utf-8")
            if not cookies:
                yield from self.start_requests()
                return
            # Load captcha url
            captcha_url = response.xpath(
                self.captcha_url_xpath).extract_first()
            captcha_url = response.urljoin(captcha_url)
            captcha = self.solve_captcha(
                captcha_url,
                response
            )
            self.logger.info(
                "Captcha has been solved: %s" % captcha
            )

            formdata = {
                'username': USER,
                'password': PASS,
                "captcha": captcha
            }

            yield FormRequest.from_response(
                response=response,
                formxpath=self.login_form_xpath,
                formdata=formdata,
                headers=self.headers,
                dont_filter=True,
                meta=self.synchronize_meta(response),
                callback=self.parse_start
            )

    def parse_start(self, response):

        if response.xpath(self.captcha_url_xpath):
            self.logger.info("Invalid Captcha")
            return
        yield from super().parse_start(response)


class SilkRoad4Scrapper(SiteMapScrapper):
    spider_class = SilkRoad4Spider
    site_name = 'silkroad4 (silkroadxjzvoyxh.onion)'
    site_type = 'forum'

    def __init__(self, kwargs):
        kwargs['get_users'] = True
        super().__init__(kwargs)

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 502],
            }
        )
        return settings
