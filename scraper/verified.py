import re
import os
import time
import traceback
from requests import Session
from lxml.html import fromstring
from scraper.base_scrapper import BaseScrapper


# Credentials
USERNAME = "NightCat"
PASSWORD = "2PK&fx2i%yL%FsIMwJaE5gfr"


# Topic Counter
TOPIC_START_COUNT = 70
TOPIC_END_COUNT = 100000

PROXY = "socks5h://localhost:9050"


class VerifiedScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super(VerifiedScrapper, self).__init__(kwargs)
        self.login_url = "http://verified2ebdpvms.onion/index.php"
        self.topic_url = "http://verified2ebdpvms.onion/showthread.php?t={}"
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
        self.ignore_xpath = '//div[@class="errorwrap"]'

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

    def do_scrape(self):
        print('**************  Started verified Scrapper **************\n')
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
