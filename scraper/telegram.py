import asyncio
import json
import os
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

def date_format(message):
    """
    :param message:
    :return:
    """
    if type(message) is datetime:
        return message.timestamp()


class TelegramChannelSpider(SitemapSpider):
    use_proxy = "Off"
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
        self.channel = kwargs['channel']
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
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
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
            self.write_message(msg_object)

    def parse_message(self):
        self.loop.run_until_complete(self.process_new_messages())
        return

    def write_message(self, msg_object):
        msg_dict = msg_object.to_dict()
        msg_dict["sender"] = msg_object.sender.to_dict()
        self.write_item(msg_dict)

    def write_item(self, item):
        with open(
                file=self.json_file,
                mode="a+"
        ) as file:
            file.write(json.dumps(item, ensure_ascii=False, default=date_format) + "\n")
        self.crawler.stats.inc_value("mainlist/detail_saved_count")
        self.logger.info(item)

    def start_write(self):
        with open(
                file=self.json_file,
                mode="w+"
        ) as file:
            file.write("")


class TelegramChannelScrapper(SiteMapScrapper):
    spider_class = TelegramChannelSpider
    site_type = 'telegram'

    def __init__(self, kwargs):
        super().__init__(kwargs)
        self.channel = kwargs.get("sitename")
        if self.channel is None:
            raise ValueError("Channel is required for telegram scraper.")

    def load_spider_kwargs(self):
        spider_kwargs = super().load_spider_kwargs()
        spider_kwargs["channel"] = self.channel
        return spider_kwargs
