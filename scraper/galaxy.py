import re
import os
import hashlib
import time
import random
import traceback
from requests import Session
from lxml.html import fromstring
from scraper.base_scrapper import BaseScrapper


# Credentials
USERNAME = "vrx9"
PASSWORD = "Night#Wall09"


PROXY = "socks5h://localhost:9050"


class GalaxyScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super(GalaxyScrapper, self).__init__(kwargs)
        self.start_url = "http://galaxy3m2mn5iqtn.onion/thewire/all"
        self.topic_url = "http://galaxy3m2mn5iqtn.onion/thewire/thread/{}"
        self.username = kwargs.get('user')
        self.password = kwargs.get('password')
        self.ignore_xpath = '//div[@class="elgg-main elgg-body" and '\
                            'not(ul[@class="elgg-list elgg-list-entity"])]'
        self.proxy = kwargs.get('proxy') or PROXY
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')

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
            '//div[@class="elgg-image-block clearfix thewire-post"]//img/@src'
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
        for topic in broken_topics:
            file_path = "{}/{}.html".format(self.output_path, topic)
            if os.path.exists(file_path):
                os.remove(file_path)
            self.process_topic(topic)

    def do_new_posts_scrape(self,):
        print('**************  New posts scan  **************')
        self.session.proxies.update({
            'http': self.proxy,
            'https': self.proxy,
        })
        new_post_url = 'http://x7bwsmcore5fmx56.onion/search.php?'\
                       'action=show_new'
        while True:
            print('Url: {}'.format(new_post_url))
            content = self.get_page_content(new_post_url)
            if not content:
                print('New posts not found')
                return
            new_topics = list()
            html_response = self.get_html_response(content)
            urls = html_response.xpath('//h3[@class="hn"]/a/@href')
            pattern = re.compile(r"id=(\d+)")
            for url in urls:
                match = pattern.findall(url)
                if not match:
                    continue
                new_topics.append(match[0])
            for topic in new_topics:
                # file_path = "{}/{}.html".format(self.output_path, topic)
                # if os.path.exists(file_path):
                #     os.remove(file_path)
                self.process_topic(topic)
            next_url = html_response.xpath(
                '//p[@class="paging"]/strong'
                '//following-sibling::a[1]/@href')
            if not next_url:
                return
            new_post_url = self.site_link + next_url[0]

    def do_scrape(self):
        self.session.proxies.update({
            'http': self.proxy,
            'https': self.proxy,
        })
        self.headers.update({
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0',
        })
        url = self.start_url
        topic_pattern = re.compile(r'/thread/(\d+)')
        while True:
            topic_list = set()
            content = self.get_page_content(url)
            if not content:
                print('No data found for:{}'.format(url))
                return
            html_response = self.get_html_response(content)
            topic_urls = html_response.xpath(
                '//a[@class="elgg-menu-content"]/@href')
            for topic_url in topic_urls:
                match = topic_pattern.findall(topic_url)
                if not match:
                    continue
                topic_list.add(match[0])

            for topic in topic_list:
                self.process_topic(topic)
            next_page_url = html_response.xpath(
                '//li/a[contains(text(), "Next")]/@href')
            if not next_page_url:
                break
            url = next_page_url[0]


def main():
    print('**************  Started galaxy Scrapper **************\n')
    template = GalaxyScrapper()
    template.do_scrape()

if __name__ == '__main__':
    main()
