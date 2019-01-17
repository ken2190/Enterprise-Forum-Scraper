import re
import os
import time
import traceback
from requests import Session
from lxml.html import fromstring


# Credentials
USERNAME = "bullet"
PASSWORD = "9VJ?ZPL392_p=Ky?"

# Topic Counter
TOPIC_START_COUNT = 20800
TOPIC_END_COUNT = 20900


class SentryMBAScrapper:
    def __init__(self, kwargs):
        self.topic_start_count = int(kwargs.get('topic_start'))
        self.topic_end_count = int(kwargs.get('topic_end')) + 1
        self.base_url = "https://sentry.mba/"
        self.login_url = self.base_url + "/member.php"
        self.topic_url = self.base_url + "showthread.php?tid={}"
        self.session = Session()
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
            "username": self.username,
            "password": self.password,
            "2facode": "",
            "remember": "",
            "submit": "Submit",
            "action": "do_login",
            "url": "https://sentry.mba/index.php",
            "my_post_key": "fd31952853b63192dddbb54ecce6ad7d",
        }
        login_response = self.session.post(self.login_url, data=payload)
        html_response = self.get_html_response(login_response.content)
        if html_response.xpath('//div[@class="errorwrap"]'):
            return False
        return True

    def get_page_content(self, url):
        time.sleep(0.5)
        try:
            response = self.session.get(url)
            content = response.content
            html_response = self.get_html_response(content)
            if html_response.xpath(
               '//div[contains(text(),'
               '"The specified thread does not exist")]'):
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
            '//span[@class="pagination_current"]'
            '/following-sibling::a[1]/@href'
        )
        if not next_page_block:
            return
        next_page_url = next_page_block[0]
        pattern = re.compile(r'tid=(\d+)&page=(\d+)')
        match = pattern.findall(next_page_url)
        if not match:
            return
        if self.base_url not in next_page_url:
            next_page_url = self.base_url + next_page_url
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
        print('**************  Sentry MBA Scrapper Started  **************\n')
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
    template = SentryMBAScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()
