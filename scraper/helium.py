import os
import re

from scrapy.exceptions import CloseSpider
from scrapy.http import Request, FormRequest

from scraper.base_scrapper import SitemapSpider, SiteMapScrapper

USERNAME = 'kylelopz'
PASSWORD = 'Password123'
PROXY = 'http://127.0.0.1:8118'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'


class HeliumSpider(SitemapSpider):
    name = 'helium_spider'

    base_url = "http://fahue6hb7odzns36vfoi2dqfvqvjq4btt7vo52a67jivmyz6a6h3vzqd.onion/"
    login_url = "http://fahue6hb7odzns36vfoi2dqfvqvjq4btt7vo52a67jivmyz6a6h3vzqd.onion/login"

    # Css stuffs
    login_form_xpath = "//form[@class='form-horizontal']"
    forum_xpath = "//a[contains(@href, '/board')]/@href"

    # Xpath stuffs
    pagination_xpath = "//a[@rel='next']/@href"
    thread_xpath = "//div[@id='recent_topics']//tbody/tr[not(@class='clearfix')]"
    post_action_xpath = "//div[contains(@class, 'thread-row')]//form[@action]/@action"
    thread_page_xpath = "//ul[@class='pagination']/li[@class='active']/span/text()"
    thread_pagination_xpath = "//a[@rel='next']/@href"
    topic_pattern = re.compile(
        r'/topic/(\d+)',
        re.IGNORECASE
    )
    # Login Failed Message
    login_failed_xpath = "//div[contains(@class,'alert-danger')]//li"

    # Other settings
    use_proxy = "Tor"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.master_list_dir = kwargs.get('master_list_path')

        if not os.path.exists(self.master_list_dir):
            os.mkdir(self.master_list_dir)
        self.headers.update({'User-Agent': USER_AGENT})

    def start_requests(self):
        """
        Send a get request to the login url to fetch the _token value
        before start login.
        """
        yield Request(
            url=self.login_url,
            headers=self.headers,
            callback=self.start_login,
            meta={
                'proxy': PROXY
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

    def start_login(self, response):
        """
        Login to the site using a given account credential.
        """
        self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        self.headers['Connection'] = 'keep-alive'
        self.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        self.headers['Accept-Encoding'] = 'gzip, deflate'
        self.headers['Upgrade-Insecure-Requests'] = '1'

        _token = response.xpath("//input[@type='hidden']/@value").extract_first()
        _captcha_img = response.xpath("//img[@id='captcha_img']/@src").extract_first()

        captcha_text = self.solve_captcha(image_url=_captcha_img,
                                          response=response)

        yield FormRequest.from_response(
            response,
            formxpath=self.login_form_xpath,
            formdata={
                "username": USERNAME,
                "password": PASSWORD,
                "remember": 'on',
                "captcha": captcha_text,
                '_token': _token
            },
            headers=self.headers,
            dont_filter=True,
            meta=self.synchronize_meta(response)
        )

    def check_parse_topic(self, topic_id, current_page, post_ids):
        """
        Check discrepancies between a list of current posts and the old posts
        obtained from a txt file named with topic_id. And then determine whether or not
        we need to parse the topic.

        :param topic_id: indicates the ID of the topic
        :param current_page: indicates the page of the topic being scraped
        :param post_ids: a list of Post IDs.
        """
        post_ids = [i.strip() for i in post_ids]
        topic_txt_file = f'{self.master_list_dir}/{topic_id}-{current_page}.txt'

        if not os.path.exists(topic_txt_file):
            # This means the topic is completely new.
            with open(topic_txt_file, 'w') as file:
                file.write(','.join(post_ids))
            return True

        with open(topic_txt_file, 'r') as file:
            post_id_str = file.read().replace('\n', '')

        old_post_ids = [i.strip() for i in post_id_str.split(',')]
        diff_ids = list(set(post_ids) ^ set(old_post_ids))

        if diff_ids:
            # Save the latest post ids in the txt file.
            with open(topic_txt_file, 'w') as file:
                file.write(','.join(post_ids))
            return True
        return False

    def parse_forum(self, response, thread_meta={}, is_first_page=True):
        self.logger.info(f'Next_page_url: {response.url}')

        threads = response.xpath(self.thread_xpath)

        for thread in threads:
            topic_url = thread.xpath(".//a[contains(@href, '/topic')]/@href").extract_first()

            yield Request(
                url=response.urljoin(topic_url),
                headers=self.headers,
                callback=self.parse_thread,
                meta=self.synchronize_meta(response)
            )

        # get next page
        next_page = self.get_forum_next_page(response)

        if is_first_page:
            self.crawler.stats.inc_value('mainlist/mainlist_processed_count')
        if next_page:
            # update stats
            if is_first_page:
                self.crawler.stats.inc_value('mainlist/mainlist_next_page_count')

            yield Request(
                url=next_page,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
                cb_kwargs={'is_first_page': False}
            )

    def get_topic_id(self, url=None):
        try:
            return self.topic_pattern.findall(url)[0]
        except:
            return ""

    def parse_thread(self, response):
        # Get topic id
        topic_id = self.get_topic_id(response.url)
        if not topic_id:
            self.crawler.stats.inc_value('mainlist/detail_no_topic_id_count')
            self.logger.warning(f'Unable to find topic ID of this topic: {response.url}')
            return
        current_page = self.get_thread_current_page(response)
        post_actions = response.xpath(self.post_action_xpath).extract()
        post_ids = [i.split('/')[-1].strip() for i in post_actions if i]
        parse_topic = self.check_parse_topic(topic_id, current_page, post_ids)

        if not parse_topic:
            # This topic doesn't have new comments, so, skipping...
            self.logger.info(f'Already parsed this topic: {response.url} so, skipping...')
            self.crawler.stats.inc_value('mainlist/detail_already_scraped_count')
            self.crawler.stats.set_value('mainlist/detail_count', len(self.topics))

        if topic_id not in self.topics:
            self.topics.add(topic_id)
            self.crawler.stats.set_value("mainlist/detail_count", len(self.topics))

        # Save thread content
        if not self.useronly:
            with open(file=os.path.join(self.output_path,
                                        f"{topic_id}-{current_page}.html"),
                      mode="w+",
                      encoding="utf-8") as file:
                file.write(response.text)
            self.logger.info(f'{topic_id}-{current_page} done..!')
            self.topic_pages_saved += 1

            # Update stats
            self.topics_scraped.add(topic_id)
            self.crawler.stats.set_value('mainlist/detail_saved_count',
                                         len(self.topics_scraped))

            # Kill task if kill count met
            if self.kill and self.topic_pages_saved >= self.kill:
                raise CloseSpider(reason='Kill count met, shut down.')

        next_page = self.get_thread_next_page(response)

        if next_page:
            self.crawler.stats.inc_value('mainlist/detail_next_page_count')

            meta = self.synchronize_meta(response)
            meta['topic_id'] = topic_id

            yield Request(
                url=next_page,
                headers=self.headers,
                callback=self.parse_thread,
                meta=meta
            )


class HeliumScrapper(SiteMapScrapper):
    spider_class = HeliumSpider
    site_name = 'helium'
    site_type = 'forum'
