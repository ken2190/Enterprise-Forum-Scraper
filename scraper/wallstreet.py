import re
import os
import hashlib
import time
import traceback
from requests import Session
from lxml.html import fromstring
from scraper.base_scrapper import BaseScrapper


# Credentials
USERNAME = "vrx9"
PASSWORD = "Night#Wall09"


# Topic Counter
TOPIC_START_COUNT = 10
TOPIC_END_COUNT = 22841

PROXY = "socks5h://localhost:9050"


class WallStreetScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super(WallStreetScrapper, self).__init__(kwargs)
        self.login_url = "http://x7bwsmcore5fmx56.onion/login.php"
        self.topic_url = "http://x7bwsmcore5fmx56.onion/viewtopic.php?id={}"
        self.username = kwargs.get('user')
        self.password = kwargs.get('password')
        self.ignore_xpath = '//p[contains(text(), '\
            '"The link you followed is incorrect or outdated")]'
        self.proxy = kwargs.get('proxy') or PROXY
        self.avatar_name_pattern = re.compile(r'.*avatars/(\w+\.\w+)')

    def write_paginated_data(self, html_response):
        next_page_block = html_response.xpath(
            '//p[@class="paging"]/strong'
            '//following-sibling::a[1]/@href'
        )
        if not next_page_block:
            return
        next_page_url = next_page_block[0]
        pattern = re.compile(r'id=(\d+)&p=(\d+)')
        match = pattern.findall(next_page_url)
        if not match:
            return
        topic, pagination_value = match[0]
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
            '//li[@class="useravatar"]/img/@src'
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
        for i in range(5):
            try:
                response = self.session.get(self.login_url).content
                break
            except:
                time.sleep(5)
                response = None
        if not response:
            return False
        html_response = self.get_html_response(response)
        token = html_response.xpath('//input[@name="csrf_token"]/@value')
        if not token:
            return False
        data = {
            'csrf_token': token[0],
            "form_sent": "1",
            "login": "Login",
            'req_password': password,
            'req_username': username,
            'save_pass': "1",
        }
        login_response = self.session.post(self.login_url, data=data)
        html_response = self.get_html_response(login_response.content)
        if html_response.xpath(
           '//span[text()="Incorrect username and/or password."]'):
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
            try:
                response = self.process_first_page(
                    topic, self.ignore_xpath
                )
                if response is None:
                    continue
                continue_xpath = '//h1[contains(text(), '\
                    '"Please refresh your page")]'
                if response.xpath(continue_xpath):
                    self.topic_start_count = topic
                    self.session = Session()
                    initial_file = '{}/{}.html'.format(self.output_path, topic)
                    if os.path.exists(initial_file):
                        os.remove(initial_file)
                    print('Initiliazing again.............')
                    return self.do_scrape()
                avatar_info = self.get_avatar_info(response)
                for name, url in avatar_info.items():
                    self.save_avatar(name, url)

                # ------------clear cookies without logout--------------
                self.clear_cookies()
            except:
                traceback.print_exc()
                continue
            self.process_pagination(response)
        return False


def main():
    print('**************  Started wallstreet Scrapper **************\n')
    template = WallStreetScrapper()
    template.do_scrape()

if __name__ == '__main__':
    main()
