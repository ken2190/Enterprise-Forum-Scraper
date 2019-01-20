import re
import os
import time
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

    def do_scrape(self):
        print('************  BreachForums Scrapper Started  ************\n')
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
    template = BreachForumsScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()
