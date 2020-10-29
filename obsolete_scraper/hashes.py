import re
import os
import scrapy
from scrapy.crawler import CrawlerProcess


USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) '\
             'AppleWebKit/537.36 (KHTML, like Gecko) '\
             'Chrome/75.0.3770.142 Safari/537.36'

DOWNLOAD_DELAY = 0.2
NO_OF_THREADS = 20
PROXY = None

OUTPUT_FOLDER = '/Users/PathakUmesh/Desktop/hashes'


class HashesSpider(scrapy.Spider):
    name = "hashes_spider"
    allowed_domains = ["hashes.org"]
    start_urls = [
        'https://hashes.org/hashlists.php',
        'https://hashes.org/leaks.php'
    ]

    def __init__(self):
        if not os.path.exists(OUTPUT_FOLDER):
            os.makedirs(OUTPUT_FOLDER)
        self.output_folder = OUTPUT_FOLDER

    def parse(self, response):
        links = response.xpath(
            '//a[button[@title="Download Founds"]]/@href'
        ).extract()
        for link in links:
            if 'https://hashes.org/' not in link:
                link = 'https://hashes.org/' + link
            hash_id = re.findall(r'hashlistId=(\d+)', link)
            output_file = os.path.join(
                self.output_folder, f'{hash_id[0]}.txt'
            )
            if os.path.exists(output_file):
                continue
            yield scrapy.Request(
                link,
                self.save_file,
                meta={'output_file': output_file}
            )

    def save_file(self, response):
        output_file = response.meta['output_file']
        with open(output_file, 'wb') as f:
            f.write(response.body)
        print(f'{output_file} done!!')


if __name__ == '__main__':
    settings = {
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
            'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': None
        },
        'USER_AGENT': USER_AGENT,
        'DOWNLOAD_DELAY': DOWNLOAD_DELAY,
        'CONCURRENT_REQUESTS': NO_OF_THREADS,
        'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
        'RETRY_HTTP_CODES': [403, 429, 500, 503],
        'RETRY_TIMES': 10,
        'LOG_ENABLED': True,

    }
    if PROXY:
        settings['DOWNLOADER_MIDDLEWARES'].update({
            'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
            'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
            'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
        })
        settings.update({
            'ROTATING_PROXY_LIST': PROXY,

        })
    process = CrawlerProcess(settings)
    process.crawl(HashesSpider)
    process.start()
