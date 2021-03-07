from scrapy import signals

class LogExceptionIntoStats:
    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()

        crawler.signals.connect(ext.spider_error, signal=signals.spider_error)

        return ext

    def spider_error(self, spider, response, failure):
        spider.crawler.stats.set_value('finish_exception', (failure.value.__class__.__qualname__, str(failure.value)))
