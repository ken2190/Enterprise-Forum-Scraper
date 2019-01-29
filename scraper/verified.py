import re
import os
import hashlib
import time
import traceback
from requests import Session
from lxml.html import fromstring
from scraper.base_scrapper import BaseScrapper


# Credentials
USERNAME = "DoZ3r"
PASSWORD = "Clp#-1O93jhfx"


# Topic Counter
TOPIC_START_COUNT = 70
TOPIC_END_COUNT = 100000

PROXY = "socks5h://localhost:9050"


class VerifiedScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super(VerifiedScrapper, self).__init__(kwargs)
        self.site_link = "http://verified2ebdpvms.onion/"
        self.login_url = self.site_link + "login.php?do=login"
        self.topic_url = self.site_link + "showthread.php?t={}"
        self.headers.update({
            'cookie': 'IDstack=52f6ee8010f343029d3c2db65073fc619b89e8b26c46ed719cb17135185ea345%3A8022b4660875732455424ca98da29997c7d26a95eece3715c8ddf86573563ef5; '
                      'bblastvisit=1547272348; '
                      'bblastactivity=0; '
                      'bbuserid=60413; '
                      'bbpassword=b36ed0f2813a0b74ddf98e709c925d67; '
                      'bbsessionhash=b44349dc1940d57af030efc8c58472c3'
        })
        self.username = kwargs.get('user')
        self.password = kwargs.get('password')
        self.ignore_xpath = '//div[contains(text(), "No Thread specified")]'

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
        # Remaining task
        # urls = html_response.xpath(
        #     '//img[@class="avatarp radius100"]/@src'
        # )
        # for url in urls:
        #     name_match = self.avatar_name_pattern.findall(url)
        #     if not name_match:
        #         continue
        #     name = name_match[0]
        #     if name not in avatar_info:
        #         avatar_info.update({
        #             name: url
        #         })
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

    def do_scrape(self):
        print('**************  Started verified Scrapper **************\n')
        # if not self.login():
        #     print('Login failed! Exiting...')
        #     return
        # print('Login Successful!')
        if not self.session.proxies.get('http'):
            self.session.proxies.update({
                'http': PROXY,
                'https': PROXY,
            })
        # ----------------go to topic ------------------
        for topic in range(self.topic_start_count, self.topic_end_count):
            try:
                response = self.process_first_page(
                    topic, self.ignore_xpath
                )
                if response is None:
                    continue

                avatar_info = self.get_avatar_info(response)
                for name, url in avatar_info.items():
                    self.save_avatar(name, url)

                # ------------clear cookies without logout--------------
                self.clear_cookies()
            except:
                traceback.print_exc()
                continue
            self.process_pagination(response)


def main():
    template = VerifiedScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()
