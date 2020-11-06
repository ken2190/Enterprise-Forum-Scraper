import os
import re
import json
import scrapy
from scrapy.http import Request, FormRequest
from datetime import datetime
from scraper.base_scrapper import SiteMapScrapper


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class PasteBinSpider(scrapy.Spider):
    name = 'pastebin_spider'
    start_url = 'https://scrape.pastebin.com/api_scraping.php?limit=250'
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS

    def __init__(self, *args, **kwargs):
        today = datetime.now().strftime('%Y-%m-%d')
        self.output_path = f'{kwargs.get("output_path")}/{today}'
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def start_requests(self):
        yield Request(
            url=self.start_url
        )

    def parse(self, response):
        json_data = json.loads(response.text)
        for data in json_data:
            paste_url = data['full_url']
            yield Request(
                url=paste_url,
                callback=self.save_paste,
                meta={'dump_id': data['key']}
            )

    def save_paste(self, response):
        dump_id = response.meta['dump_id']
        dump_file = '{}/{}.txt'.format(
            self.output_path, dump_id
        )
        if os.path.exists(dump_file):
            print('{} already exists..!'.format(dump_file))
            return

        content = response.xpath(
            '//textarea[@id="paste_code"]/text()').extract()
        content = ''.join(content)
        with open(dump_file, 'w') as f:
            f.write(content)
        print('{} done..!'.format(dump_file))


class PasteBinScrapper(SiteMapScrapper):

    spider_class = PasteBinSpider
    site_name = 'pastebin.com'
    site_type = 'paste'
