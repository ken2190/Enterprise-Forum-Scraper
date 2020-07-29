import re
import os
import json
import asyncio
import time

from scrapy.signals import spider_closed
from telethon import TelegramClient
from pydispatch import dispatcher

from datetime import (
    datetime,
    timedelta
)
from scrapy import (
    Request,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


api_id = "1366434"
api_hash = "1a4bc8ae740923572b1d7bd9bc9dbe08"

class TelegramChannelSpider(SitemapSpider):

    name = "telegramss"

    # Url stuffs
    channel_url = "https://t.me/s/%s"

    # Other settings
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"
    chunk = 10  # Change this to change number of messages per request
    delay = 1  # Change the delay between each request

    def spider_closed(self, spider):
        self.stop_write()

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

        # Init file
        self.start_write()

    def start_requests(self):
        yield Request(
            url=self.channel_url % self.channel
        )


    def parse(self, response):
        yield from self.parse_message()

    def parse_message(self, max_id=None):

        # Init queue
        if not max_id:
            messages_queue = self.client.get_messages(self.channel, limit=self.chunk)
        else:
            messages_queue = self.client.get_messages(self.channel, limit=self.chunk, max_id=max_id)

        # Execute queue
        messages = self.loop.run_until_complete(messages_queue)

        # Yield message
        for message in messages:
            # Check date
            if self.start_date and message.date.replace(tzinfo=None) < self.start_date:
                self.logger.info(
                    "Find no more message later than %s, ignoring." % self.start_date
                )
                return

            yield from self.process_message(message.__dict__)

        # Load max id
        if messages:
            max_id = messages[-1].id

            # Delay before next request
            time.sleep(self.delay)

            yield from self.parse_message(max_id=max_id)

    def process_message(self, message):

        # Init item
        item = {
            "date": message.get("date").strftime(self.post_datetime_format)
        }

        # Update item
        item.update(
            {
                key: value for key, value in message.items()
                if type(value) in [str, int]
            }
        )

        yield from self.write_item(item)

    def write_item(self, item):
        with open(
            file=self.json_file,
            mode="a+",
            encoding="utf-8"
        ) as file:
            if not self.first_write:
                self.first_write = True
            else:
                file.write(",")
            file.write(json.dumps(item))
        yield item

    def start_write(self):
        with open(
            file=self.json_file,
            mode="w+",
            encoding="utf-8"
        ) as file:
            file.write("[")

    def stop_write(self):
        with open(
                file=self.json_file,
                mode="a+",
                encoding="utf-8"
        ) as file:
            file.write("]")


class TelegramChannelScrapper(SiteMapScrapper):
    spider_class = TelegramChannelSpider

    def __init__(self, kwargs):
        super().__init__(kwargs)
        self.channel = kwargs.get("channel")
        if self.channel is None:
            raise ValueError("Channel is required for telegram scraper.")

    def load_spider_kwargs(self):
        spider_kwargs = super().load_spider_kwargs()
        spider_kwargs["channel"] = self.channel
        return spider_kwargs
