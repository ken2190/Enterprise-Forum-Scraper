import re
import os
import time
import traceback
from requests import Session
from lxml.html import fromstring


# Credentials
USERNAME = "NightCat"
PASSWORD = "2PK&fx2i%yL%FsIMwJaE5gfr"


# Topic Counter
TOPIC_START_COUNT = 100
TOPIC_END_COUNT = 1000

PROXY = "socks5h://localhost:9050"


class VerifiedScrapper:
    def __init__(self, kwargs):
        self.topic_start_count = TOPIC_START_COUNT
        self.topic_end_count = TOPIC_END_COUNT
        self.login_url = "http://verified2ebdpvms.onion/index.php"
        self.topic_url = "http://verified2ebdpvms.onion/showthread.php?t={}"
        self.session = Session()
        self.session.proxies = {}
        self.session.proxies['http'] = kwargs.get('proxy')
        self.session.proxies['https'] = kwargs.get('proxy')
        self.output_path = kwargs.get('output')
        self.username = kwargs.get('user')
        self.password = kwargs.get('password')

    def get_html_response(self, content):
        html_response = fromstring(content)
        return html_response

    def login(self):
        if not self.username:
            self.username = USERNAME
        if not self.password:
            self.password = PASSWORD
        payload = {
            'vb_login_username': self.username,
            'vb_login_password': self.password,
        }
        login_response = self.session.post(self.login_url, data=payload)
        html_response = self.get_html_response(login_response.content)
        if html_response.xpath('//form[@action="register.php"]'):
            return False
        return True

    def get_page_content(self, url):
        time.sleep(0.5)
        try:
            response = self.session.get(url)
            content = response.content
            html_response = self.get_html_response(content)
            if html_response.xpath('//div[@class="errorwrap"]'):
                return
            return content
        except:
            return

    def process_first_page(self, topic):
        url = self.topic_url.format(topic)
        content = self.get_page_content(url)
        if not content:
            print('No data for url: {}'.format(url))
            return

        initial_file = '{}/{}.html'.format(self.output_path, topic)
        with open(initial_file, 'wb') as f:
            f.write(content)
        print('{} done..!'.format(topic))
        html_response = self.get_html_response(content)
        return html_response

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

        content = self.get_page_content(next_page_url)
        if not content:
            return

        paginated_file = '{}/{}-{}.html'.format(
            self.output_path, topic, pagination_value
        )
        with open(paginated_file, 'wb') as f:
            f.write(content)

        print('{}-{} done..!'.format(topic, pagination_value))
        return content

    def process_pagination(self, response):
        while True:
            paginated_content = self.write_paginated_data(response)
            if not paginated_content:
                return
            response = self.get_html_response(paginated_content)

    def clear_cookies(self,):
        self.session.cookies['topicsread'] = ''

    def do_scrape(self):
        print('**************  Started verified Scrapper **************\n')
        if not self.session.proxies['http']:
            print('Proxy required...')
            return
        if not self.login():
            print('Login failed! Exiting...')
            return
        print('Login Successful!')
        # ----------------go to topic ------------------
        for topic in range(self.topic_start_count, self.topic_end_count):
            try:
                response = self.process_first_page(topic)
                if response is None:
                    continue

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
