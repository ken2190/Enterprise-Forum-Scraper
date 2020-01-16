import re
import os
import hashlib
import time
import random
import traceback
from requests import Session
from lxml.html import fromstring
from scraper.base_scrapper import BaseTorScrapper


# Credentials
USERNAME = "vrx9"
PASSWORD = "Night#Vrx099"


# Topic Counter
TOPIC_START_COUNT = 70
TOPIC_END_COUNT = 100000


class VerifiedScrapper(BaseTorScrapper):
    def __init__(self, kwargs):
        super().__init__(kwargs)
        self.site_link = "http://verified2ebdpvms.onion/"
        self.login_url = self.site_link + "login.php?do=login"
        self.topic_url = self.site_link + "showthread.php?t={}"
        self.headers.update({
            'cookie': 'IDstack=db57dd63d50b537ca89882f289e6950d7d72de45bde0a73358837ed729e0935a; '
                      'bblastvisit=1549534014; '
                      'bblastactivity=0; '
                      'bbuserid=62675; '
                      'bbpassword=edc7e2c6b7bfe17463f5f875c244d79c; '
                      'bbsessionhash=b44349dc1940d57af030efc8c58472c3'
        })
        self.username = kwargs.get('user') or USERNAME
        self.password = kwargs.get('password') or PASSWORD
        self.ignore_xpath = '//div[contains(text(), "No Thread specified")]'
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')

    def write_paginated_data(self, html_response):
        next_page_block = html_response.xpath(
            '//div[@class="pagenav"]'
            '//td[span/strong]'
            '//following-sibling::td[1]/a/@href'
        )
        if not next_page_block:
            return
        next_page_url = next_page_block[0]
        pattern = re.compile(r't=(\d+)&page=(\d+)')
        match = pattern.findall(next_page_url)
        if not match:
            return
        topic, pagination_value = match[0]
        if self.site_link not in next_page_url:
            next_page_url = self.site_link + next_page_url
        content = self.get_page_content(
            next_page_url, self.ignore_xpath
        )
        if not content:
            return

        paginated_file = '{}/{}-{}.html'.format(
            self.output_path, topic, pagination_value
        )
        with open(paginated_file, 'wb') as f:
            f.write(content)

        print('{}-{} done..!'.format(topic, pagination_value))
        return content

    def clear_cookies(self,):
        self.session.cookies['topicsread'] = ''

    def get_avatar_info(self, html_response):
        avatar_info = dict()
        urls = html_response.xpath(
            '//img[contains(@alt, "Avatar")]/@src'
        )
        for url in urls:
            url = self.site_link + url
            name_match = self.avatar_name_pattern.findall(url)
            if not name_match:
                continue
            name = name_match[0]
            if name not in avatar_info:
                avatar_info.update({
                    name: url
                })
        return avatar_info

    def login(self):
        password = self.password or PASSWORD
        md5_pass = hashlib.md5(password.encode('utf-8')).hexdigest()
        payload = {
            "do": "login",
            "s": "",
            "securitytoken": "guest",
            "url": "/forum.php",
            "vb_login_md5password": md5_pass,
            "vb_login_md5password_utf": md5_pass,
            "vb_login_password": "",
            "vb_login_username": self.username or USERNAME
        }
        login_response = self.session.post(self.login_url, data=payload)
        html_response = self.get_html_response(login_response.content)
        if html_response.xpath('//form[@action="register.php"]'):
            return False
        return True

    def process_topic(self, topic):
        try:
            response = self.process_first_page(
                topic, self.ignore_xpath
            )
            if response is None:
                return

            avatar_info = self.get_avatar_info(response)
            for name, url in avatar_info.items():
                self.save_avatar(name, url)

            # ------------clear cookies without logout--------------
            self.clear_cookies()
        except:
            traceback.print_exc()
            return
        self.process_pagination(response)

    def do_new_posts_scrape(self,):
        print('**************  New posts scan  **************')
        print('Implementation not complete yet!!')

    def do_rescan(self,):
        print('**************  Rescanning  **************')
        print('Broken Topics found')
        broken_topics = self.get_broken_file_topics()
        print(broken_topics)
        if not broken_topics:
            return
        self.session.proxies.update({
            'http': self.proxy,
            'https': self.proxy,
        })
        random.shuffle(broken_topics)
        for topic in broken_topics:
            file_path = "{}/{}.html".format(self.output_path, topic)
            if os.path.exists(file_path):
                os.remove(file_path)
            self.process_topic(topic)

    def do_scrape(self):
        print('**************  Started verified Scrapper **************\n')

        if not self.session.proxies.get('http'):
            self.session.proxies.update({
                'http': self.proxy,
                'https': self.proxy,
            })
        # ----------------go to topic ------------------
        ts = self.topic_start_count or TOPIC_START_COUNT
        te = self.topic_end_count or TOPIC_END_COUNT + 1
        topic_list = list(range(ts, te))
        random.shuffle(topic_list)
        for topic in topic_list:
            self.process_topic(topic)


def main():
    template = VerifiedScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()
