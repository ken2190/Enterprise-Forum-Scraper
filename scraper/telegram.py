import re
import os
import json

from scrapy.signals import spider_closed
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


class TelegramChannelSpider(SitemapSpider):

    name = "phreaker_spider"

    # Url stuffs
    base_url = "https://t.me"
    channel_url = "https://t.me/s/%s"

    # Xpath stuffs
    message_xpath = "//div[contains(@class,\"tgme_widget_message_wrap\")]"
    pagination_xpath = "//a[@data-before]/@href"
    single_mapper = {
        "pid": "//div[@data-post]/@data-post",
        "author": "//span[@dir=\"auto\"]/text()",
        "author_url": "//a[@class=\"tgme_widget_message_owner_name\"]/@href",
        "content": "//div[@class=\"tgme_widget_message_text js-message_text\"]",
        "post_date": "//a[@class=\"tgme_widget_message_date\"]/time/@datetime",
        "views": "//span[@class=\"tgme_widget_message_views\"]/text()",
        "preview_url": "//a[@class=\"tgme_widget_message_link_preview\"]/@href",
        "preview_site_name": "//div[@class=\"link_preview_site_name\"]/text()",
        "preview_title": "//div[@class=\"link_preview_title\"]/text()"
    }
    multiple_mapper = {
        "preview_content": "//div[@class=\"link_preview_description\"]/text()"
    }

    # Other settings
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    def parse_post_date(self, post_date):
        return super().parse_post_date(post_date[:-6])

    def spider_closed(self, spider):
        self.stop_write()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dispatcher.connect(self.spider_closed, spider_closed)
        self.channel = kwargs.get("channel")
        self.first_write = False

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

    def get_post_date(self, message):
        # Load selector
        selector = Selector(text=message)

        return self.parse_post_date(
            selector.xpath(
                self.single_mapper.get("post_date")
            ).extract_first()
        )

    def start_requests(self):
        yield Request(
            url=self.channel_url % self.channel,
            headers=self.headers,
            callback=self.parse
        )

    def parse(self, response):

        # Load all messages
        all_messages = response.xpath(self.message_xpath).extract()
        for message in all_messages:
            yield from self.parse_message(message)

        # Pagination
        pagination_url = response.xpath(self.pagination_xpath).extract_first()
        last_date = max(
            [
                self.get_post_date(message) for message in all_messages
            ]
        )

        if not pagination_url:
            self.logger.info(
                "Found no more page, aborting."
            )
            return
        if self.start_date and last_date < self.start_date:
            self.logger.info(
                "No more post before %s, aborting." % self.start_date
            )
            return

        yield Request(
            url=self.base_url + pagination_url,
            headers=self.headers,
            callback=self.parse
        )

    def parse_message(self, message):

        # Load selector
        selector = Selector(text=message)

        # Load single item
        item = {
            key: selector.xpath(xpath).extract_first()
            for key, xpath in self.single_mapper.items()
        }

        # Load multiple item
        item.update(
            {
                key: selector.xpath(xpath).extract()
                for key, xpath in self.multiple_mapper.items()
            }
        )

        # Handle preview contents
        if item.get("preview_content"):
            item["preview_content"] = "\n".join(item.get("preview_content"))
        else:
            item["preview_content"] = None

        # Yield standardize item
        yield from self.write_item(
            {
                key: value.strip() for key, value in item.items()
                if value is not None
            }
        )

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
