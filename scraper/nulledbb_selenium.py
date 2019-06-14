import os
import re
import traceback
from threading import Thread
from multiprocessing import Queue, cpu_count

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from time import sleep
from lxml.html import fromstring

FORUM_URLS = [
    'https://nulledbb.com/forum-Announcements-News-Information',
    'https://nulledbb.com/forum-The-Lounge',
    'https://nulledbb.com/forum-Gaming',
    'https://nulledbb.com/forum-Crypto-Currency',
    'https://nulledbb.com/forum-Entertainment',
    'https://nulledbb.com/forum-Other-Discussions',
    'https://nulledbb.com/forum-Introductions',
    'https://nulledbb.com/forum-Member-Contests-Giveaways',
    'https://nulledbb.com/forum-Milestones-Achievements',
    'STOP'
]


def get_response(worker, url):
    while True:
        try:
            worker.get(url)
            return
        except:
            # worker.close()
            print('Retrying....')
            sleep(1)


class NulledBBScrapper():
    def __init__(self, kwargs):
        self.output_folder = kwargs.get('output')
        self.base_url = 'https://nulledbb.com/'
        self.set_threads()

    def set_threads(self):
        self.url_queue = Queue()
        self.worker_queue = Queue()
        worker_ids = list(range(cpu_count()))
        # worker_ids = [0]
        options = Options()
        options.add_argument("start-maximized")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        self.selenium_workers = {
            i: webdriver.Chrome(chrome_options=options) for i in worker_ids
        }
        for worker_id in worker_ids:
            self.worker_queue.put(worker_id)

        self.selenium_processes = [
            Thread(
                target=self.selenium_queue_listener,
            )
            for _ in worker_ids
        ]

    def do_scrape(self):
        for p in self.selenium_processes:
            p.daemon = True
            p.start()
        for url in FORUM_URLS:
            self.url_queue.put(url)
        for p in self.selenium_processes:
            p.join()
        for b in self.selenium_workers.values():
            b.quit()

    def selenium_queue_listener(self):
        while True:
            current_url = self.url_queue.get()
            if current_url == 'STOP':
                self.url_queue.put(current_url)
                break
            worker_id = self.worker_queue.get()
            worker = self.selenium_workers[worker_id]
            self.each_tab_task(worker, current_url)
            self.worker_queue.put(worker_id)
        return

    def each_tab_task(self, worker, url):
        get_response(worker, url)
        sleep(10)
        print(f'FORUM URL: {url}')
        self.process_forum(worker)

    def process_forum(self, worker):
        print('Processing Forum')
        data = worker.page_source
        html_response = fromstring(data)
        threads = html_response.xpath(
            '//span[contains(@class, "subject_") and contains(@id, "tid_")]/a')
        for thread in threads:
            title = thread.xpath('text()')[0]
            title = str(
                int.from_bytes(
                    title.encode('utf-8'), byteorder='big'
                ) % (10 ** 7)
            )
            file_path = f'{self.output_folder}/{title}-1.html'
            if os.path.exists(file_path):
                continue
            link = thread.xpath('@href')[0]
            if self.base_url not in link:
                link = self.base_url + link
            self.process_thread(worker, link, file_path)
        paginated_link = self.get_paginated_link(html_response)
        if not paginated_link:
            return
        get_response(worker, paginated_link)
        sleep(2)
        print(f'\nFORUM URL: {paginated_link}')
        self.process_forum(worker)

    def process_thread(self, worker, link, file_path):
        get_response(worker, link)
        data = worker.page_source
        with open(file_path, 'wb') as f:
            f.write(data.encode('utf-8'))
        print(f'Saved data for {link.rsplit("thread-", 1)[-1]} '
              f'as {file_path.rsplit("/", 1)[-1]}')
        html_response = fromstring(data)
        paginated_link = self.get_paginated_link(html_response)
        if not paginated_link:
            return
        paginated_value = paginated_link.split('page=')[-1]
        file_path = re.sub(r'-(\d+)', f'-{paginated_value}', file_path)
        return self.process_thread(worker, paginated_link, file_path)

    def get_paginated_link(self, html_response):
        pagination = html_response.xpath('//a[@class="pagination_next"]/@href')
        if not pagination:
            return
        link = pagination[0]
        if self.base_url not in link:
            link = self.base_url + link
        return link
