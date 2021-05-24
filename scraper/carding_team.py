import os
import re
import time
import uuid
import json

from datetime import datetime
from scrapy.utils.gz import gunzip

from seleniumwire.webdriver import (
    Chrome,
    ChromeOptions
)
from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

USERNAME = 'MrSnow'
PASSWORD = 'C1rh_2hf81!d'


class CardingTeamSpider(SitemapSpider):
    name = 'cardingteam_spider'

    # Url stuffs
    base_url = "https://cardingteam.is/"
    login_url = f'{base_url}member.php?action=login'

    # Xpath stuffs
    login_form_xpath = '//form[@action="member.php"]'
    forum_xpath = '//tbody//a[contains(@href, "Forum-")]/@href'
    pagination_xpath = '//div[@class="pagination"]' \
                       '/a[@class="pagination_next"]/@href'
    thread_xpath = '//tr[@class="inline_row"]'
    thread_pagination_xpath = '//div[@class="pagination"]' \
                              '//a[@class="pagination_next"]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'

    # Login Failed Message
    login_failed_xpath = '//div[contains(@class, "error")]'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "On"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.master_list_dir = kwargs.get('master_list_path')

        if not os.path.exists(self.master_list_dir):
            os.mkdir(self.master_list_dir)

    @staticmethod
    def get_thread_info(thread_element):
        """
        Extract the thread URL and ID from the given thread_element.
        """
        subject_element = thread_element.xpath(".//span[contains(@class, 'subject_old')]")
        thread_url = subject_element.xpath('.//a/@href').extract_first()
        thread_id = subject_element.xpath('@id').extract_first()
        thread_id = thread_id.replace('tid_', '').strip()

        return thread_id, thread_url

    @staticmethod
    def get_post_ids(response):
        """
        Extract post IDs from new posts in the page.
        """
        post_ids = response.xpath("//div[@class='newposts']/a/@id").extract()
        post_ids = [i.replace('pid', '').strip() for i in post_ids]

        return post_ids

    def check_parse_topic(self, topic_id, post_ids):
        """
        Check discrepancies between a list of current posts and the old posts
        obtained from a txt file named with topic_id. And then determine whether or not
        we need to parse the topic.

        :param topic_id: indicates the ID of the topic
        :param post_ids: a list of Post IDs.
        """
        topic_txt_file = f'{self.master_list_dir}/{topic_id}.txt'

        if not os.path.exists(topic_txt_file):
            # This means the topic is completely new.
            with open(topic_txt_file, 'w') as file:
                file.write(','.join(post_ids))
            return True

        with open(topic_txt_file, 'r') as file:
            post_id_str = file.read().replace('\n', '')

        old_post_ids = [i.strip() for i in post_id_str.split(',')]

        if not set(post_ids) <= set(old_post_ids):
            post_ids = list(set(old_post_ids + post_ids))
            # Save the latest post ids in the txt file.
            with open(topic_txt_file, 'w') as file:
                file.write(','.join(post_ids))
            return True
        return False

    def start_requests(self):
        """
        Send a get request to the login url to fetch the _token value
        before start login.
        """
        yield Request(
            url=self.login_url,
            headers=self.headers,
            callback=self.start_login
        )

    def start_login(self, response):
        """
        Login to the site using a given account credential.
        """
        self.synchronize_headers(response)

        form_data = {
            'username': USERNAME,
            'password': PASSWORD,
        }

        yield FormRequest.from_response(
            response=response,
            formxpath=self.login_form_xpath,
            formdata=form_data,
            headers=self.headers,
            meta=self.synchronize_meta(response)
        )

    def parse_forum(self, response, thread_meta={}, is_first_page=True):
        self.logger.info(f'Page_url: {response.url}')

        threads = response.xpath(self.thread_xpath)

        for thread in threads:
            thread_id, thread_url = self.get_thread_info(thread)

            # Check thread meta
            if thread_meta:
                meta = thread_meta
            else:
                meta = self.synchronize_meta(response)

            meta['topic_id'] = thread_id

            yield Request(
                url=response.urljoin(thread_url),
                headers=self.headers,
                callback=self.parse_thread,
                meta=meta
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

    def parse_thread(self, response):
        self.synchronize_headers(response)

        topic_id = response.meta['topic_id']

        post_ids = self.get_post_ids(response)
        parse_topic = self.check_parse_topic(topic_id, post_ids)

        if not parse_topic:
            # This topic doesn't have new comments, so, skipping...
            self.logger.info(f'Already parsed this thread: {response.url} so, skipping...!')
            self.crawler.stats.inc_value('mainlist/detail_already_scraped_count')
            self.crawler.stats.set_value('mainlist/detail_count', len(self.topics))

        if topic_id not in self.topics:
            self.topics.add(topic_id)
            self.crawler.stats.set_value('mainlist/detail_count', len(self.topics))

        # Save thread content
        if parse_topic and not self.useronly:
            current_page = self.get_thread_current_page(response)

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

            # Parse generic avatar
            yield from super().parse_avatars(response)

            # Kill task if kill count met
            if self.kill and self.topic_pages_saved >= self.kill:
                raise CloseSpider(reason='Kill count met, shut down.')

        # get next page
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


class CardingTeamScrapper(SiteMapScrapper):
    spider_class = CardingTeamSpider
    site_name = 'cardingteam.cc'
    site_type = 'forum'
