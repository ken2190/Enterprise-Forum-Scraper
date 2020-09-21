import re
from scrapy.http import Request, FormRequest
from scraper.base_scrapper import SiteMapScrapper, SitemapSpider

USER = 'Cyrax_011'
PASS = 'Night#India065'

PROXY = 'http://127.0.0.1:8118'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 '\
             'Firefox/68.0'


class DNMAvengersSpider(SitemapSpider):
    name = 'dnmavengers_spider'

    base_url = 'http://avengersdutyk3xf.onion/'
    login_url = 'http://avengersdutyk3xf.onion/member.php'

    forum_xpath = '//a[contains(@href, "forum-")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[@class="pagination_next"]/@href'
    thread_xpath = '//tr[@class="inline_row"]'
    thread_first_page_xpath = '//span[contains(@id,"tid_")]/a/@href'
    thread_last_page_xpath = '//td[contains(@class,"forumdisplay_")]/div'\
                             '/span/span[contains(@class,"smalltext")]'\
                             '/a[last()]/@href'
    thread_date_xpath = '//td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/text()[1]|'\
                        '//td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/span/@title'
    thread_pagination_xpath = '//div[@class="pagination"]'\
                              '//a[@class="pagination_previous"]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//span[@class="post_date"]/text()[1]'\

    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'

    # regex stuffs
    topic_pattern = re.compile(r'thread-(\d+)')
    avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
    pagination_pattern = re.compile(r'page-(\d+)')

    use_proxy = False

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml'
                  ';q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': base_url,
        'User-Agent': USER_AGENT,
    }

    def start_requests(self):
        yield Request(
            url=self.base_url,
            callback=self.process_login,
            meta={'proxy': PROXY}
        )

    def process_login(self, response):
        my_post_key = response.xpath(
            '//input[@name="my_post_key"]/@value').extract_first()
        if not my_post_key:
            return
        form_data = {
            'username': USER,
            'password': PASS,
            'remember': 'yes',
            'action': 'do_login',
            'url': '/index.php',
            'my_post_key': my_post_key,
        }
        yield FormRequest(
            url=self.login_url,
            formdata=form_data,
            callback=self.parse,
            meta=self.synchronize_meta(response),
            headers=self.headers,
            dont_filter=True,
        )

    def parse_thread(self, response):

        yield from super().parse_thread(response)

        yield from super().parse_avatars(response)

class DNMAvengersScrapper(SiteMapScrapper):

    request_delay = 0.1
    no_of_threads = 16

    spider_class = DNMAvengersSpider
    site_name = 'DNM Avengers (avengersdutyk3xf.onion)'

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': self.request_delay,
                'CONCURRENT_REQUESTS': self.no_of_threads,
                'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads
            }
        )
        return spider_settings
