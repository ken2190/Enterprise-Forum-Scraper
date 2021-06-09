import base64
import os
import re

from scrapy import (
    Request,
    FormRequest
)
from datetime import datetime
from scraper.base_scrapper import (
    MarketPlaceSpider,
    SiteMapScrapper
)

MIN_DELAY = 1.5
MAX_DELAY = 2
DAILY_LIMIT = 10000

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'

PROXY = 'http://127.0.0.1:8118'


class DarkFoxSpider(MarketPlaceSpider):
    name = "darkfox_spider"

    # Url stuffs
    base_url = "http://57d5j6hfzfpsfev6c7f5ltney5xahudevvttfmw4lrtkt42iqdrkxmqd.onion/"

    # xpath stuffs
    captch_form_xpath = '//form[@method="post"]'
    captcha_url_xpath_1 = '//div[@class="imgWrap"]/@style'
    captcha_url_xpath_2 = '//img[contains(@class, "captcha")]/@src'
    market_url_xpath = '//input[@name="category[]"]/@value'
    product_url_xpath = '//div[@class="media-content"]/a[contains(@href, "/product/")]/@href'

    next_page_xpath = '//a[@rel="next"]/@href'
    user_xpath = '//h3[contains(., "Vendor:")]/a/@href'
    user_description_xpath = '//div[@class="tabs"]//a[contains(@href, "/about")]/@href'
    user_pgp_xpath = '//div[@class="tabs"]//a[contains(@href, "/pgp")]/@href'
    avatar_xpath = '//ul[@class="slides"]//img[contains(@class, "slide-main")]/@src'

    # Login Failed Message xpath
    captcha_failed_xpath_1 = captcha_url_xpath_1
    captcha_failed_xpath_2 = captcha_url_xpath_2

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )
    use_proxy = "Tor"
    retry_count = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.master_list_path = kwargs.get('master_list_path')
        if not os.path.exists(self.master_list_path):
            os.mkdir(self.master_list_path)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )

    def get_captcha_image_content(self, image_url, cookies={}, headers={}, proxy=None):

        # Separate the metadata from the image data
        head, data = image_url.split(',', 1)

        # Decode the image data
        plain_data = base64.b64decode(data)

        return plain_data

    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip"]
            if response.meta.get(key)
        }

        meta.update(default_meta)
        meta.update({'proxy': PROXY})

        return meta

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse_captcha_1,
            errback=self.check_site_error,
            dont_filter=True,
            meta={
                'proxy': PROXY,
                'handle_httpstatus_list': [302],
                'next_callback': self.parse_start
            }
        )

    def get_market_url(self, category_id):
        return f'{self.base_url}category/{category_id}'

    def get_product_next_page(self, response):
        next_page_url = response.xpath(self.next_page_xpath).extract_first()
        if not next_page_url:
            return
        if self.base_url not in next_page_url:
            next_page_url = self.base_url + next_page_url
        return next_page_url

    def parse_captcha_1(self, response, next_callback=None):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        if not next_callback:
            next_callback = response.meta.get('next_callback')

        # Load cookies
        cookies = response.request.headers.get("Cookie")
        if not cookies:
            self.retry_count += 1
            if self.retry_count <= 5:
                yield from self.start_requests()
                self.logger.info(
                    f"Retry #{self.retry_count} to load main page."
                )
            return

        # Load captcha url
        captcha_url = response.xpath(
            self.captcha_url_xpath_1).extract_first()
        if not captcha_url:
            self.logger.info(
                "Captcha url not found."
            )
            return
        captcha = self.solve_captcha(
            captcha_url,
            response
        )
        if not captcha:
            self.logger.info(
                "Did not get a captcha solution from solve_captcha."
            )
            return
        captcha = captcha.lower()
        self.logger.info(
            "Captcha has been solved: %s" % captcha
        )

        formdata = {
            "cap": captcha
        }
        self.logger.debug(f'Form data: {formdata}')

        yield FormRequest.from_response(
            response=response,
            formxpath=self.captch_form_xpath,
            formdata=formdata,
            headers=self.headers,
            callback=next_callback,
            dont_filter=True,
            meta=self.synchronize_meta(response),
        )

    def parse_captcha_2(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Check if bypass captcha failed
        self.check_if_captcha_failed(response, self.captcha_failed_xpath_1)

        # Load cookies
        cookies = response.request.headers.get("Cookie")
        # Load captcha url
        captcha_url = response.xpath(
            self.captcha_url_xpath_2).extract_first()
        captcha = self.solve_captcha(
            captcha_url,
            response
        )
        captcha = captcha.lower()
        self.logger.info(
            "Captcha has been solved: %s" % captcha
        )

        token = response.xpath('//input[@name="_token"]/@value').extract_first()
        formdata = {
            "_token": token,
            "captcha": captcha
        }
        self.logger.debug(f'Form data: {formdata}')

        yield FormRequest.from_response(
            response=response,
            formxpath=self.captch_form_xpath,
            formdata=formdata,
            headers=self.headers,
            callback=self.parse_start,
            dont_filter=True,
            meta=self.synchronize_meta(response),
        )

    def parse_start(self, response):

        # Check if bypass captcha failed
        self.check_if_captcha_failed(response, self.captcha_failed_xpath_2)

        captcha_1 = response.xpath(self.captcha_url_xpath_1).extract()
        if captcha_1:
            yield from self.parse_captcha_1(
                response,
                self.parse_start
            )

        yield from super().parse_start(response)

    def parse_products(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        captcha_1 = response.xpath(self.captcha_url_xpath_1).extract()
        if captcha_1:
            yield from self.parse_captcha_1(
                response,
                self.parse_products
            )

        self.logger.info('next_page_url: {}'.format(response.url))
        products = response.xpath(self.product_url_xpath).extract()

        self.crawler.stats.inc_value("mainlist/detail_count", len(products))

        for product_url in products:
            product_url = self.get_product_url(product_url)
            if not product_url:
                self.crawler.stats.inc_value("mainlist/detail_no_url_count")
                self.logger.warning(
                    "Unable to find product URL on the marketplace: %s",
                    response.url
                )
                continue

            file_id = self.get_file_id(product_url)
            product_txt_file = f'{self.master_list_path}/{file_id}.txt'
            if os.path.exists(product_txt_file):
                self.crawler.stats.inc_value("mainlist/product_already_in_master_list")
                self.logger.info(f'{product_url} already scraped. Skipping.')
                continue

            file_name = '{}/{}.html'.format(self.output_path, file_id)
            
            self.crawler.stats.inc_value("mainlist/detail_next_page_count")
            self.crawler.stats.inc_value("mainlist/mainlist_processed_count")

            if os.path.exists(file_name):
                continue
            yield Request(
                url=product_url,
                headers=self.headers,
                callback=self.parse_product,
                dont_filter=True,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        'file_id': file_id
                    }
                )
            )
        next_page_url = self.get_product_next_page(response)
        if next_page_url:
            self.crawler.stats.inc_value("mainlist/mainlist_next_page_count")

            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_products,
                dont_filter=True,
                meta=self.synchronize_meta(response),
            )

    def parse_product(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        captcha_1 = response.xpath(self.captcha_url_xpath_1).extract()
        if captcha_1:
            yield from self.parse_captcha_1(
                response,
                self.parse_product
            )

        if "file_id" in response.meta:
            file_id = response.meta['file_id']
        else:
            file_id = self.get_file_id(response.request.url)

        file_name = '{}/{}.html'.format(self.output_path, file_id)
        product_txt_file = f'{self.master_list_path}/{file_id}.txt'
        with open(file_name, 'wb') as f, open(product_txt_file, 'w') as file:
            f.write(response.text.encode('utf-8'))
            file.write(f'{datetime.now().isoformat()}')
            self.logger.info(f'Product: {file_id} done..!')
            self.crawler.stats.inc_value("mainlist/detail_saved_count")

        response.meta['file_id'] = file_id
        if self.avatar_xpath:
            yield from self.parse_avatars(response)


class DarkFoxScrapper(SiteMapScrapper):
    spider_class = DarkFoxSpider
    site_name = 'darkfox (57d5j6hfzfpsfev6c7f5ltney5xahudevvttfmw4lrtkt42iqdrkxmqd)'
    site_type = 'marketplace'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "AUTOTHROTTLE_ENABLED": True,
                "AUTOTHROTTLE_START_DELAY": MIN_DELAY,
                "AUTOTHROTTLE_MAX_DELAY": MAX_DELAY,
                "CLOSESPIDER_PAGECOUNT": DAILY_LIMIT
            }
        )
        return settings
