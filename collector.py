import argparse
from config import main_parser_arguments
from parser import Parser
from config import main_parser_arguments


class Collector:

    def __init__(self):
        self.parser = Parser(description='Framework For Scrapping Forums', arguments=main_parser_arguments)

    def start(self):
        kwargs = self.parser.get_args()
        if kwargs.get('parse'):
            from forumparse import Parser
            Parser(kwargs).start()
        elif kwargs.get('scrape'):
            from run_scrapper import Scraper
            Scraper(kwargs).do_scrape()
        elif kwargs.get("gather"):
            # from noscrape_engine import Gatherer
            # Gatherer.start()
            pass
        elif kwargs.get("scan"):
            from noscrape_v1.noscrape_v1 import NoScrapeV1
            NoScrapeV1(kwargs).run()
        else:
            self.parser.print_help()


if __name__ == '__main__':
    Collector().start()
