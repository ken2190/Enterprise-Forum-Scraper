import argparse
import sh


class Collector:

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Scrapping Forums Framework'
        )
        
        # Main arguments
        parser.add_argument(
            '-scrape', '--scrape', help='Do scraping',
            action='store_true')
        parser.add_argument(
            '-parse', '--parse', help='Do parsing',
            action='store_true')
        parser.add_argument(
            '-gather', '--gather', help='Do gather db ip',
            action='store_true'
        )
        parser.add_argument(
            '-scan','--scan', help='Do scan db ip port',
            action='store_true'
        )

        # Scraper and parser branch
        scraper_options = parser.add_argument_group('Scraper Options')
        scraper_options.add_argument(
            '-t', '--template', help='Template forum to scrape', required=False)
        scraper_options.add_argument(
            '-p', '--path', help='input folder path', required=False)
        scraper_options.add_argument(
            '-o', '--output', help='output folder path', required=False)
        scraper_options.add_argument(
            '-uo', '--useronly', help='Scrape only users page', action='store_true')
        scraper_options.add_argument(
            '-s', '--start_date', help='Scrape from the given dates', required=False)
        scraper_options.add_argument(
            '-ch', '--channel', help='Channel to scrape (For telegram template)', required=False)
        scraper_options.add_argument(
            '-k', '--kill', help='Kill after this amount of topic page saved', required=False)
        
        self.parser = parser

    def get_args(self):
        args, unknown = self.parser.parse_known_args()
        return args._get_kwargs()

    def start(self):
        kwargs = {k: v for k, v in self.get_args()}
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
            from noscrape_engine import Noscraper
            Noscraper().do_scrape()
        else:
            self.parser.print_help()


if __name__ == '__main__':
    Collector().start()
