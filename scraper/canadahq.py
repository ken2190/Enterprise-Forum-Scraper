import os
import re
import uuid

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

USERNAME = "blastedone"
PASSWORD = "Chq#Blast888"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36"


class CanadaHQSpider(SitemapSpider):

    name = "canadahq_spider"

    # Url stuffs
    base_url = "https://canadahq.net/"
    login_url = "https://canadahq.net/login"

    # Css stuffs
    login_form_css = "form[action*=login]"
    captcha_url_css = "div>img[src*=captcha]::attr(src)"

    # Xpath stuffs
    invalid_captcha_xpath = "//div[@class=\"alert alert-danger\"]/" \
                            "span/text()[contains(.,\"Invalid captcha\")]"

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
    use_proxy = False
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    captcha_instruction = "Please ignore | and ^"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )

    def parse(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        yield Request(
            url=self.login_url,
            headers=self.headers,
            dont_filter=True,
            meta=self.synchronize_meta(response),
            callback=self.parse_login
        )

    def parse_login(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load cookies
        cookies = response.request.headers.get("Cookie").decode("utf-8")
        if "XSRF-TOKEN" not in cookies:
            yield Request(
                url=self.login_url,
                headers=self.headers,
                dont_filter=True,
                meta=self.synchronize_meta(response),
                callback=self.parse_login
            )
            return

        # Load captcha url
        captcha_url = response.css(self.captcha_url_css).extract_first()
        captcha = self.solve_captcha(
            captcha_url,
            response
        )
        if len(captcha) > 5:
            captcha = captcha.replace('l', '').replace('^', '')

        self.logger.info(
            "Captcha has been solved: %s" % captcha
        )

        yield FormRequest.from_response(
            response,
            formcss=self.login_form_css,
            formdata={
                "username": USERNAME,
                "password": PASSWORD,
                "captcha": captcha[:5]
            },
            headers=self.headers,
            meta=self.synchronize_meta(response),
            callback=self.parse_start
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        # Check valid captcha
        is_invalid_captcha = response.xpath(
            self.invalid_captcha_xpath).extract_first()
        if is_invalid_captcha:
            self.logger.info(
                "Invalid captcha."
            )
            return

        self.logger.info(response.text)

        urls = response.xpath(
            '//div[@class="menu-content"]/ul/li/a')
        for url in urls:
            url = url.xpath('@href').extract_first()
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_results
            )

    def parse_results(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        self.logger.info('next_page_url: {}'.format(response.url))
        products = response.xpath(
            '//a[@class="product"]')
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

        next_page = response.xpath('//a[@rel="next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_results
            )

    def parse_product(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        file_id = response.meta['file_id']
        file_name = '{}/{}.html'.format(self.output_path, file_id)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'Product: {file_id} done..!')

        user_url = response.xpath(
            '//a[contains(text(), "profile") and contains(text(), "View")]'
            '/@href').extract_first()
        if not user_url:
            return
        user_id = user_url.rsplit('/', 1)[-1]
        file_name = '{}/{}.html'.format(self.user_path, user_id)
        if os.path.exists(file_name):
            return
        yield Request(
            url=user_url,
            headers=self.headers,
            callback=self.parse_user,
            meta=self.synchronize_meta(
                response,
                default_meta={
                    'file_name': file_name,
                    'user_id': user_id
                }
            )
        )

    def parse_user(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        user_id = response.meta['user_id']
        file_name = response.meta['file_name']
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'User: {user_id} done..!')

        avatar_url = response.xpath(
            '//img[@class="img-responsive"]/@src').extract_first()
        if not avatar_url:
            return
        ext = avatar_url.rsplit('.', 1)[-1]
        if not ext:
            ext = 'jpg'
        file_name = '{}/{}.{}'.format(self.avatar_path, user_id, ext)
        if os.path.exists(file_name):
            return
        yield Request(
            url=avatar_url,
            headers=self.headers,
            callback=self.parse_avatar,
            meta=self.synchronize_meta(
                response,
                default_meta={
                    'file_name': file_name,
                    'user_id': user_id
                }
            )
        )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        with open(file_name, 'wb') as f:
            f.write(response.body)
            self.logger.info(
                f"Avatar for user {response.meta['user_id']} done..!")


class CanadaHQScrapper(SiteMapScrapper):
    spider_class = CanadaHQSpider
    site_name = 'canadahq.at'
