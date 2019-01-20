import re
import os
import traceback
from scraper.base_scrapper import BaseScrapper

# Topic Counter
TOPIC_START_COUNT = 56700
TOPIC_END_COUNT = 56800


class AntichatScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super(AntichatScrapper, self).__init__(kwargs)
        self.site_link = "https://forum.antichat.ru/"
        self.topic_url = self.site_link + "threads/{}/"
        self.ignore_xpath = '//label[contains(text(),'\
                            '"The requested thread could not be found")]'

    def write_paginated_data(self, html_response):
        next_page_block = html_response.xpath(
            '//a[contains(@class,"currentPage")]'
            '/following-sibling::a[1]/@href'
        )
        if not next_page_block:
            return
        next_page_url = self.site_link + next_page_block[0]\
            if self.site_link not in next_page_block[0]\
            else next_page_block[0]
        pattern = re.compile(r"threads/(\d+)/page-(\d+)")
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
        print('**************  Antichat Scrapper Started  **************\n')
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
    template = AntichatScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()
