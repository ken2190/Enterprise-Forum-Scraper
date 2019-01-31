import re
import os
import time
import random
import traceback
from scraper.base_scrapper import BaseScrapper


# Topic Counter
TOPIC_START_COUNT = 500
TOPIC_END_COUNT = 900


class BreachForumsScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super(BreachForumsScrapper, self).__init__(kwargs)
        self.site_link = "https://breachforums.com/"
        self.topic_url = self.site_link + "showthread.php?tid={}"
        self.ignore_xpath = '//td[contains(text(),'\
                            '"The specified thread does not exist")]'
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')

    def write_paginated_data(self, html_response):
        next_page_block = html_response.xpath(
            '//span[@class="pagination_current"]'
            '/following-sibling::a[1]/@href'
        )
        if not next_page_block:
            return
        next_page_url = self.site_link + next_page_block[0]\
            if self.site_link not in next_page_block[0]\
            else next_page_block[0]
        pattern = re.compile(r"tid=(\d+)&page=(\d+)")
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

    def do_scrape(self):
        print('************  BreachForums Scrapper Started  ************\n')
        # ----------------go to topic ------------------
        ts = self.topic_start_count or TOPIC_START_COUNT
        te = self.topic_end_count or TOPIC_END_COUNT + 1
        topic_list = list(range(ts, te))
        random.shuffle(topic_list)
        for topic in topic_list:
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
    template = BreachForumsScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()
