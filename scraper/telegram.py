import asyncio
import json
import os
import re
from datetime import (
    datetime
)

from pydispatch import dispatcher
from scrapy import (
    Request
)
from scrapy.signals import spider_closed
from telethon import TelegramClient

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

api_id = "13722063"
api_hash = "9a3a3479661523ed348ffdc463ef33a1"


class TelegramChannelSpider(SitemapSpider):
    name = "telegramss"

    # Url stuffs
    channel_url = "https://t.me/s/%s"

    # Other settings
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    def spider_closed(self, spider):
        self.logger.info("Spider closed successfully.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dispatcher.connect(self.spider_closed, spider_closed)
        self.channel = kwargs.get("channel")
        self.first_write = False

        # Init client
        self.client = TelegramClient(self.name, api_id, api_hash).start()

        # Init loop
        self.loop = asyncio.get_event_loop()

        # Load file date
        end_date = datetime.today().strftime(
            "%m_%d_%Y"
        )
        if self.start_date:
            start_date = self.start_date.strftime(
                "%m_%d_%Y"
            )
        else:
            start_date = "begin"

        # Load file path
        json_file = "telegram_channel_%s_from_%s_to_%s.json" % (
            self.channel,
            start_date,
            end_date
        )
        self.json_file = os.path.join(
            self.output_path,
            json_file
        )

    def start_requests(self):
        yield Request(
            url=self.channel_url % self.channel
        )

    def parse(self, response):
        self.parse_message()
        return

    async def process_new_messages(self):
        async for msg_object in self.client.iter_messages(self.channel):
            if msg_object.message is None:
                continue
            if msg_object.date.timestamp() < self.start_date.timestamp():
                self.logger.info(f'Stopping as date of message is {msg_object.date}')
                break

            # Init item
            self.process_message(msg_object)

    def parse_message(self):
        self.loop.run_until_complete(self.process_new_messages())
        return

    def process_message(self, msg_object):
        sender = msg_object.sender
        # Init item
        message = msg_object.message
        item = {"channel": self.channel, "type": "telegram", "date": msg_object.date.timestamp() * 1000,
                "author": sender.username, "message": message, "urls": self.extract_urls(message),
                "usernames": self.extract_usernames(message)}
        doc = {"_source": item}
        # Update item
        self.write_item(doc)

    def write_item(self, item):
        with open(
                file=self.json_file,
                mode="a+"
        ) as file:
            file.write(json.dumps(item, indent=4, ensure_ascii=False) + "\n")
        self.crawler.stats.inc_value("mainlist/detail_saved_count")
        self.logger.info(item)

    def start_write(self):
        with open(
                file=self.json_file,
                mode="w+"
        ) as file:
            file.write("")

    def extract_urls(self, message):
        url_pattern = r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b"
        res = re.findall(url_pattern, message)
        if res:
            return res
        else:
            return []

    def extract_usernames(self, message):
        username_pattern = r"@([^\s:,\.]+)"
        res = re.findall(username_pattern, message)
        if res:
            return res
        else:
            return []


class TelegramChannelScrapper(SiteMapScrapper):
    spider_class = TelegramChannelSpider
    site_type = 'telegram'

    def __init__(self, kwargs):
        super().__init__(kwargs)
        self.channel = kwargs.get("channel")
        if self.channel is None:
            raise ValueError("Channel is required for telegram scraper.")

    def load_spider_kwargs(self):
        spider_kwargs = super().load_spider_kwargs()
        spider_kwargs["channel"] = self.channel
        return spider_kwargs
