import os
import re
import uuid
import base64
import requests
from urllib.parse import unquote

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    MarketPlaceSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5

USERNAME = "blastedone"
PASSWORD = "Chq#Blast888"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36"

PROXY = 'http://127.0.0.1:8118'


class EmpireSpider(MarketPlaceSpider):

    name = "empire_spider"

    # Url stuffs
    urls = [
        'http://oz3jlxp4oymxt4rzuzm266fvc357fnmwzvm7iigjmntxim2w4m43s2ad.onion',
        'http://xhhk37ey4yal7mcgv5b6f2mwtgysh5zpm6o2j33s4htosik3nobobmid.onion',
        'http://sgxye32vhffhn7d3twtgicbchznimd6guj27pyou7jhosmxttan7c2id.onion',
        'http://cdtqz6ip57l6ugctdq33z6hr63xanlxtmpjbvzayygow6b4hkdvuctqd.onion',
        'http://vxyl2wkhkmtjpvbb3eia26vdzhaphrr7dbf6ovwjqy63f27vjffjwiyd.onion',
        'http://erj7kwqkdkl73ewsuq6stztehx2tehk2aidxlex3btrfnjqax3ucvgyd.onion',
        'http://p3f5jyqooy3pqzmugzxq2fwcxmdttkshn57nca4pserrcvw6xj5mrfid.onion',
        'http://m4itbrzwruzzzqfjie6ygxzqnqnjxhq6d24hyjpvyk7qdtycckr73mad.onion',
        'http://wlwcklts7mes5zcs2muzgorikvdp44mpvjglpenphqo2jwvofr75xvad.onion',
        'http://uvkxwkpeemv4frvju6ks5wveec5bxljfibknuioejpjkl3oq2up55lyd.onion',
        'http://igoz2dm6vqo3nuweg3vztqszxprugx2lb6xxbrmz2tkec37gc2vkd5yd.onion',
        'http://piifyattgybu3a2rwx675ptqzeb4f7sfjxslx6n4a7kccijlksxzroqd.onion',
        'http://k7lwzkbirsizhvtrmafqzy7ut47junhdczab3766kok2xc3odvzdijad.onion',
        'http://sczojdk73hhztnyc6omdelztijoejf2sucfvpwfzazgvgvsbsobo5dqd.onion',
        'http://6o6vpjt6di2nf5lykqssx4e5wnjw7pjaq4ja6dsyx2onuadevqgcbjad.onion',
        'http://i5kjii2y2jumlye6etmouksvdhech357urmj4txctrneedl4vkfjbsqd.onion',
        'http://p4e6p65pal3s4zrva3q3gk44s3ejl7futx47qserb2slcwyjj7sao4id.onion',
        'http://jfjkkvra7753bp7czrooipdeacc3ptwmeuurlbb3d42ntngonhq7ycad.onion',
    ]

    # xpath stuffs
    login_form_xpath = '//form[@method="post"]'
    captcha_instruction = 'Black characters only'
    captcha_url_xpath = '//img[contains(@src, "captchaimg")]/@src'
    invalid_captcha_xpath = '//p[@class="invalidCaptchaError"]/text()'
    market_url_xpath = '//a[contains(@href, "/categories/")]/@href'
    product_url_xpath = '//a[contains(@href, "/product/")]/@href'
    next_page_xpath = '//a[@rel="next"]/@href'
    user_xpath = '//a[contains(@href, "/u/")]/@href'
    avatar_xpath = '//div[@class="user_info_left"]/img/@src'
    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    use_proxy = True
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )

    def get_base_url(self, ):
        proxies = {'https': PROXY, 'http': PROXY}
        for url in self.urls:
            self.logger.info(f'Trying url: {url}')
            try:
                r = requests.get(url, proxies=proxies, timeout=15)
                if 'placeholder="Username"' in r.text:
                    return url
            except Exception:
                continue

    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip"]
            if response.meta.get(key)
        }

        meta.update(default_meta)
        meta.update({'proxy': PROXY})

        return meta

    def get_user_id(self, url):
        return url.rsplit('u/', 1)[-1]

    def get_file_id(self, url):
        return url.rsplit('product/', 1)[-1].replace('/', '')

    def start_requests(self):
        self.base_url = self.get_base_url()
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
        userfield = response.xpath(
            '//input[@placeholder="Username"]/@name').extract_first()
        passfield = response.xpath(
            '//input[@placeholder="Password"]/@name').extract_first()
        captchafield = response.xpath(
            '//input[contains(@placeholder, "captcha")]/@name').extract_first()

        # Load cookies
        cookies = response.request.headers.get("Cookie").decode("utf-8")
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
        self.logger.info(
            "Captcha has been solved: %s" % captcha
        )

        formdata = {
            userfield: USERNAME,
            passfield: PASSWORD,
            captchafield: captcha
        }
        print(formdata)

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

        yield from super().parse_start(response)


class EmpireScrapper(SiteMapScrapper):
    spider_class = EmpireSpider
    site_name = 'empire (uhjru3mxpre7fgrmhdyd3c7kaenkzov3bxaiezp5pnsoxoqehhszi5yd.onion)'
    site_type = 'marketplace'
