
from config import main_parser_arguments
from cli_parser import CliParser
from config import main_parser_arguments


class Collector:

    def __init__(self):
        self.parser = CliParser(description='Framework For Scrapping Forums', arguments=main_parser_arguments)

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
            from noscrape.noscrape import NoScrape
            NoScrape(kwargs).run()
        elif kwargs.get("post"):
            from tools import post_process
            post_process.run()
        else:
            self.parser.print_help()

if __name__ == '__main__':
    Collector().start()
