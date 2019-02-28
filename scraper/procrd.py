import re
import os
import time
import traceback
import requests
from requests import Session
from scraper.base_scrapper import BaseScrapper

RCKID = "bbP582dxEPHSqPT3uc5dQj7lZCvRCpDwESaZBH6RIpb6f96lu9n9RazTomhx6vru"
BLAZINGFAST_WEB_PROTECT = "771fc8bbf99b93989e22bd21242af073"


class ProcrdScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super(ProcrdScrapper, self).__init__(kwargs)
        self.base_url = 'https://procrd.me/'
        self.topic_pattern = re.compile(r'.*\.(\d+)/')
        self.comment_pattern = re.compile(r'(\<\!--.*?--\!\>)')
        self.cloudfare_error = None
        cookie = f"rcksid={RCKID}; "\
            f"BLAZINGFAST-WEB-PROTECT={BLAZINGFAST_WEB_PROTECT};"
        self.headers = {
            "cookie": cookie,
            "referer": "https://procrd.me/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/72.0.3626.119 Safari/537.36"
        }

    def get_page_content(self, url):
        time.sleep(self.wait_time)
        try:
            response = requests.get(url, headers=self.headers)
            if not response.url == url:
                return self.get_page_content(response.url)
            content = response.content
            html_response = self.get_html_response(content)
            if html_response.xpath('//div[@class="errorwrap"]'):
                return
            return content
        except:
            traceback.print_exc()
            return

    def save_avatar(self, name, url):
        avatar_file = f'{self.avatar_path}/{name}'
        if os.path.exists(avatar_file):
            return
        content = self.get_page_content(url)
        if not content:
            return
        with open(avatar_file, 'wb') as f:
            f.write(content)

    def process_first_page(self, topic_url):
        topic = self.topic_pattern.findall(topic_url)
        if not topic:
            return
        topic = topic[0]
        initial_file = f'{self.output_path}/{topic}-1.html'
        if os.path.exists(initial_file):
            return
        content = self.get_page_content(topic_url)
        if not content:
            print(f'No data for url: {topic_url}')
            return
        with open(initial_file, 'wb') as f:
            f.write(content)
        print(f'{topic}-1 done..!')
        content = self.comment_pattern.sub('', str(content))
        html_response = self.get_html_response(content)
        if html_response.xpath(
            '//font[contains(text(), "Verifying your browser, please wait")]'
        ):
            print('DDOS identified. Retrying after a min')
            time.sleep(60)
            return self.process_first_page(topic_url)
        avatar_info = self.get_avatar_info(html_response)
        for name, url in avatar_info.items():
            self.save_avatar(name, url)
        return html_response

    def process_topic(self, topic_url):
        html_response = self.process_first_page(topic_url)
        if html_response is None:
            return
        while True:
            response = self.write_paginated_data(
                html_response, topic_url)
            if response is None:
                return
            topic_url, html_response = response

    def write_paginated_data(self, html_response, topic_url):
        next_page_block = html_response.xpath(
            '//a[contains(@class,"currentPage")]'
            '/following-sibling::a[1]/@href'
        )
        if not next_page_block:
            next_page_block = html_response.xpath(
                '//a[contains(@class,"currentPage")]'
                '/following-sibling::span[1]//a/@href'
            )
        if not next_page_block:
            next_page_block = html_response.xpath(
                '//a[@class="PageNavNext hidden"]'
                '/following-sibling::a[1]/@href'
            )
        if not next_page_block:
            return
        next_page_url = next_page_block[0]
        next_page_url = self.base_url + next_page_url\
            if self.base_url not in next_page_url else next_page_url
        if next_page_url == topic_url:
            return
        pattern = re.compile(r'.*\.(\d+)/page-(\d+)')
        match = pattern.findall(next_page_url)
        if not match:
            return
        topic, pagination_value = match[0]
        content = self.get_page_content(next_page_url)
        if not content:
            return
        paginated_file = f'{self.output_path}/{topic}-{pagination_value}.html'
        with open(paginated_file, 'wb') as f:
            f.write(content)

        print(f'{topic}-{pagination_value} done..!')
        content = self.comment_pattern.sub('', str(content))
        html_response = self.get_html_response(content)
        avatar_info = self.get_avatar_info(html_response)
        for name, url in avatar_info.items():
            self.save_avatar(name, url)
        return next_page_url, html_response

    def process_forum(self, url):
        while True:
            print(f"Forum URL: {url}")
            forum_content = self.get_page_content(url)
            if not forum_content:
                print(f'No data for url: {forum_content}')
                return
            forum_content = self.comment_pattern.sub('', str(forum_content))
            html_response = self.get_html_response(forum_content)
            topic_blocks = html_response.xpath(
                '//ol[@class="discussionListItems"]/li')
            if not topic_blocks:
                topic_blocks = html_response.xpath(
                    '//div[@class="uix_stickyThreads"]/li')
            for topic in topic_blocks:
                topic_url = topic.xpath(
                    'div//h3[@class="title"]/'
                    'a[contains(@href, "threads/")]/@href')
                if not topic_url:
                    continue
                topic_url = topic_url[0]
                topic_url = self.base_url + topic_url\
                    if self.base_url not in topic_url else topic_url
                self.process_topic(topic_url)
            forum_pagination_url = html_response.xpath(
                '//a[contains(@class,"currentPage")]'
                '/following-sibling::a[1]/@href'
            )
            if not forum_pagination_url:
                forum_pagination_url = html_response.xpath(
                    '//a[contains(@class,"currentPage")]'
                    '/following-sibling::span[1]//a/@href'
                )
            if not forum_pagination_url:
                forum_pagination_url = html_response.xpath(
                    '//a[@class="PageNavNext hidden"]'
                    '/following-sibling::a[1]/@href'
                )
            if not forum_pagination_url:
                return
            new_url = forum_pagination_url[0]
            new_url = self.base_url + new_url\
                if self.base_url not in new_url else new_url
            if new_url == url:
                return
            url = new_url

    def get_forum_urls(self, html_response):
        urls = set()
        extracted_urls = html_response.xpath(
            '//div[@class="nodeText"]'
            '/h3[@class="nodeTitle"]/a/@href'
        )
        for _url in extracted_urls:
            if self.base_url not in _url:
                urls.add(self.base_url + _url)
            else:
                urls.add(_url)
        extracted_urls = html_response.xpath(
            '//li/div/h4[@class="nodeTitle"]/a/@href'
        )
        for _url in extracted_urls:
            if self.base_url not in _url:
                urls.add(self.base_url + _url)
            else:
                urls.add(_url)
        urls = sorted(
            urls,
            key=lambda x: int(x.rsplit('.', 1)[-1].split('/')[0]))
        return urls

    def clear_cookies(self,):
        self.session.cookies.clear()

    def get_avatar_info(self, html_response):
        avatar_info = dict()
        urls = html_response.xpath(
            '//a[@data-avatarhtml="true"]/img/@src'
        )
        for url in urls:
            url = self.base_url + url\
                if not url.startswith('http') else url
            if "image.php" in url:
                avatar_name_pattern = re.compile(r'.*\.(\d+)/')
                name_match = avatar_name_pattern.findall(url)
                if not name_match:
                    continue
                name = f'{name_match[0]}.jpg'
            else:
                avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
                name_match = avatar_name_pattern.findall(url)
                if not name_match:
                    continue
                name = name_match[0]

            if name not in avatar_info:
                avatar_info.update({
                    name: url
                })
        return avatar_info

    def do_scrape(self):
        print('************  ProcrdScrapper Started  ************\n')
        main_content = self.get_page_content(self.base_url)
        if not main_content:
            print(f'No data for url: {self.base_url}')
            return
        html_response = self.get_html_response(main_content)
        forum_urls = self.get_forum_urls(html_response)
        # print(forum_urls)
        # return
        # forum_urls = ['https://procrd.me/forums/pravila-foruma-reklama-rules-advertisement.5/']
        for forum_url in forum_urls:
            self.process_forum(forum_url)


def main():
    template = ProcrdScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()
