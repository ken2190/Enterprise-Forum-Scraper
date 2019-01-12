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
TOPIC_START_COUNT = 208130
TOPIC_END_COUNT = 208230

PROXY = "socks5h://localhost:9050"


class VerifiedScrapper:
    def __init__(self, kwargs):
        self.topic_start_count = int(kwargs.get('topic_start'))
        self.topic_end_count = int(kwargs.get('topic_end')) + 1
        self.login_url = "http://verified2ebdpvms.onion/index.php"
        self.topic_url = "http://verified2ebdpvms.onion/showthread.php?t={}"
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/71.0.3578.98 Safari/537.36',
            'cookie': 'IDstack=52f6ee8010f343029d3c2db65073fc619b89e8b26c46ed719cb17135185ea345%3A8022b4660875732455424ca98da29997c7d26a95eece3715c8ddf86573563ef5; '
                      'bblastvisit=1547272348; '
                      'bblastactivity=0; '
                      'bbuserid=60413; '
                      'bbpassword=b36ed0f2813a0b74ddf98e709c925d67; '
                      'bbsessionhash=b44349dc1940d57af030efc8c58472c3'
        }
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

    def get_page_content(self, url):
        time.sleep(0.5)
        try:
            response = self.session.get(url, headers=self.headers)
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
