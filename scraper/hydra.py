import os
import re
import uuid
import base64

from urllib.parse import unquote

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'

PROXY = 'http://127.0.0.1:8118'


class HydraSpider(SitemapSpider):

    name = "hydramarket_spider"

    # Url stuffs
    base_url = "http://hydraruzxpnew4af.onion"

    # xpath stuffs
    captch_form_xpath = '//form[@method="post"]'
    captcha_url_xpath = '//img[@alt="Captcha image"]/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700
        }
    }
    use_proxy = False
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            callback=self.parse_captcha,
            dont_filter=True,
            meta={
                'proxy': PROXY,
                'handle_httpstatus_list': [302]
            }
        )

    def parse_captcha(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load cookies

        cookies = response.request.headers.get("Cookie")
        if not cookies:
            yield from self.start_requests()
            return

        # Load captcha url
        captcha_url = response.xpath(
                self.captcha_url_xpath).extract_first()
        captcha = self.solve_captcha(
            captcha_url,
            response
        )
        captcha = captcha.lower()
        self.logger.info(
            "Captcha has been solved: %s" % captcha
        )

        formdata = {
            "captcha": captcha
        }

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
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        if response.xpath(self.captcha_url_xpath):
            self.logger.info("Invalid Captcha")
            return
        urls = response.xpath(
            '//div/a[@role and contains(@href, "/market/")]')
        for url in urls:
            url = url.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_results,
                meta=self.synchronize_meta(response),
            )

    def parse_results(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        self.logger.info('next_page_url: {}'.format(response.url))
        products = response.xpath(
            '//div[@class="title over"]/a[contains(@href, "/product/")]')
        for product in products:
            product_url = product.xpath('@href').extract_first()
            if self.base_url not in product_url:
                product_url = self.base_url + product_url
            file_id = product_url.rsplit('/', 1)[-1]
            file_name = '{}/{}.html'.format(self.output_path, file_id)
            if os.path.exists(file_name):
                continue
            yield Request(
                url=product_url,
                headers=self.headers,
                callback=self.parse_product,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        'file_id': file_id
                    }
                )
            )

        next_page = response.xpath(
            '//ul[@class="pagination"]/li[@class="pag_right"]/a')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_results,
                meta=self.synchronize_meta(response),
            )

    def parse_product(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        file_id = response.meta['file_id']
        file_name = '{}/{}.html'.format(self.output_path, file_id)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'Product: {file_id} done..!')


class HydraScrapper(SiteMapScrapper):
    spider_class = HydraSpider
    site_name = 'hydra_hydraruzxpnew4af'
