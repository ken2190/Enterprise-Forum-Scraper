import re
import os
import hashlib
import time
import traceback
from requests import Session
from lxml.html import fromstring
from scraper.base_scrapper import BaseScrapper


# Credentials
USERNAME = "ironsheik"
PASSWORD = "KA-Ir0np3ss!"


# Topic Counter
TOPIC_START_COUNT = 6727
TOPIC_END_COUNT = 6729

PROXY = "socks5h://localhost:9050"


class KickAssScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super(KickAssScrapper, self).__init__(kwargs)
        self.site_link = "http://qoodvrvo2dq72sygqrvm4ymx2zwojplom4m6giiggob"\
                         "f3dpt5up24did.onion/"
        self.index_url = self.site_link + "index.php"
        self.login_url = self.site_link + "member.php"
        self.topic_url = self.site_link + "showthread.php?tid={}"
        self.username = kwargs.get('user')
        self.password = kwargs.get('password')
        self.ignore_xpath = '//td[contains(text(), '\
            '"The specified thread does not exist")]'
        self.proxy = kwargs.get('proxy') or PROXY
        self.avatar_name_pattern = re.compile(r'.*avatars/(\w+\.\w+)')
        self.headers.update({
            'user-agent': "Mozilla/5.0 (Windows NT 6.1; rv:60.0) "
                          "Gecko/20100101 Firefox/60.0"
        })

    def write_paginated_data(self, html_response):
        next_page_block = html_response.xpath(
            '//span[@class="pagination_current"]'
            '//following-sibling::a[1]/@href'
        )
        if not next_page_block:
            return
        next_page_url = next_page_block[0]
        if self.site_link not in next_page_url:
            next_page_url = self.site_link + next_page_url
        pattern = re.compile(r'id=(\d+)&page=(\d+)')
        match = pattern.findall(next_page_url)
        if not match:
            return
        topic, pagination_value = match[0]
        time.sleep(1)
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
            '//div[@class="author_avatar"]/a/img/@src'
        )
        for url in urls:
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
        username = self.username or USERNAME
        response = self.session.get(self.index_url, headers=self.headers).content
        # for i in range(5):
        #     try:
        #         response = self.session.get(self.login_url).content
        #         break
        #     except:
        #         time.sleep(5)
        #         response = None
        # if not response:
        #     return False
        html_response = self.get_html_response(response)
        my_post_key = html_response.xpath(
            '//input[@name="my_post_key"]/@value')
        if not my_post_key:
            print('11111')
            print(response)
            return False
        data = {
            "action": "do_login",
            "my_post_key": my_post_key[0],
            "password": password,
            "url": "/index.php",
            "username":    username,
        }

        login_response = self.session.post(
            self.login_url,
            data=data,
            headers=self.headers
        )
        html_response = self.get_html_response(login_response.content)
        if html_response.xpath(
           '//span[text()="Incorrect username and/or password."]'):
            print('22222222')
            print(login_response.content)
            return False
        return True

    def do_scrape(self):
        self.session.proxies.update({
            'http': self.proxy,
            'https': self.proxy,
        })
        if not self.login():
            print('Login failed! Exiting...')
            return
        print('Login Successful!')
        # ----------------go to topic ------------------
        for topic in range(self.topic_start_count, self.topic_end_count):
            time.sleep(1)
            try:
                response = self.process_first_page(
                    topic, self.ignore_xpath
                )
                if response is None:
                    continue
                avatar_info = self.get_avatar_info(response)
                for name, url in avatar_info.items():
                    time.sleep(2)
                    self.save_avatar(name, url)
                # ------------clear cookies without logout--------------
                self.clear_cookies()
            except:
                traceback.print_exc()
                continue
            self.process_pagination(response)
        return False


def main():
    print('**************  Started Kickass Scrapper **************\n')
    template = KickAssScrapper()
    template.do_scrape()

if __name__ == '__main__':
    main()
