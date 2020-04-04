import re
import json
import requests
import uuid
from urllib.parse import urlencode
import dateparser
from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)
from scrapy.http import HtmlResponse


REQUEST_DELAY = 0.3
NO_OF_THREADS = 5

USER = "Cyrax011"
PASS = "4hr63yh38a61SDW0"


class OpencardSpider(SitemapSpider):
    name = 'opencard_spider'

    # Url stuffs
    base_url = "https://opencard.us"

    # Xpath stuffs
    login_form_xpath = 'form[@method="post"]'
    forum_xpath = '//h3[@class="node-title"]/a/@href|'\
                  '//a[contains(@class,"subNodeLink--forum")]/@href'
    thread_xpath = '//div[contains(@class, "structItem structItem--thread")]'
    thread_first_page_xpath = '//div[@class="structItem-title"]'\
                              '/a[contains(@href,"threads/")]/@href'
    thread_last_page_xpath = '//span[@class="structItem-pageJump"]'\
                             '/a[last()]/@href'
    thread_date_xpath = '//time[contains(@class, "structItem-latestDate")]'\
                        '/@datetime'
    pagination_xpath = '//a[contains(@class,"pageNav-jump--next")]/@href'
    thread_pagination_xpath = '//a[contains(@class, "pageNav-jump--prev")]'\
                              '/@href'
    thread_page_xpath = '//li[contains(@class, "pageNav-page--current")]'\
                        '/a/text()'
    post_date_xpath = '//div/a/time[@datetime]/@datetime'

    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'

    # Recaptcha stuffs
    recaptcha_site_key_xpath = '//div[@data-xf-init="re-captcha"]/@data-sitekey'

    # Regex stuffs
    topic_pattern = re.compile(
        r"threads/.*\.(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.strip()[:-5]
        if not thread_date:
            return
        return dateparser.parse(thread_date)

    def parse_post_date(self, post_date):
        post_date = post_date.strip()[:-5]
        return dateparser.parse(post_date)

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                "cookiejar": uuid.uuid1().hex
            },
            dont_filter=True
        )

    def parse(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load token
        match = re.findall(r'csrf: \'(.*?)\'', response.text)

        # Load param
        params = {
            '/login': '',
            '_xfRequestUri': '/index.php',
            '_xfWithData': '1',
            '_xfToken': match[0],
            '_xfResponseType': 'json'
        }
        token_url = 'https://opencard.us/index.php?login/&' + urlencode(params)
        yield Request(
            url=token_url,
            headers=self.headers,
            callback=self.proceed_for_login,
            meta=self.synchronize_meta(response)
        )

    def proceed_for_login(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)
        # Load json data
        json_response = json.loads(response.text)
        html_response = HtmlResponse(
            url='test', body=json_response['html']['content'], encoding='utf-8')

        # Exact token
        token = html_response.xpath(
            '//input[@name="_xfToken"]/@value').extract_first()

        # Load params
        params = {
            'login': USER,
            'password': PASS,
            'remember': '1',
            'g-recaptcha-response': self.solve_recaptcha(response, html_response),
            '_xfRedirect': 'https://opencard.us/index.php',
            '_xfToken': token
        }
        login_url = 'https://opencard.us/index.php?login/login'
        yield FormRequest(
            url=login_url,
            callback=self.parse_start,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
            meta=self.synchronize_meta(response)
            )

    def solve_recaptcha(self, response, html_response):
        """
        :param response: scrapy response => response that contains regular recaptcha
        :return: str => recaptcha solved token to submit login
        """
        # Init session
        session = requests.Session()

        # Load proxy
        proxy = self.load_proxies(response)
        if proxy:
            session.proxies = {
                "http": proxy,
                "https": proxy
            }

        # Init site url and key
        site_url = response.url
        site_key = html_response.xpath(self.recaptcha_site_key_xpath).extract_first()

        try:
            jobID = self.request_solve_recaptcha(
                session,
                site_url,
                site_key
            )
            return self.request_job_recaptcha(jobID)
        except RuntimeError:
            raise (
                "2Captcha: reCaptcha solve took to long to execute, aborting."
            )

    def parse_start(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()

        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            yield Request(
                url=forum_url,
                headers=self.headers,
                meta=self.synchronize_meta(response),
                callback=self.parse_forum
            )

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class OpencardScrapper(SiteMapScrapper):

    spider_class = OpencardSpider
    site_name = 'opencard.us'

    def load_settings(self):
        spider_settings = super().load_settings()
        return spider_settings
