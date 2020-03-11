import argparse


class Collector:

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Scrapping Forums Framework')
        parser.add_argument(
            '-scrape', '--scrape', help='Do scraping',
            action='store_true')
        parser.add_argument(
            '-parse', '--parse', help='Do parsing',
            action='store_true')
        parser.add_argument(
            '-t', '--template', help='Template forum to scrape', required=False)
        parser.add_argument(
            '-p', '--path', help='input folder path', required=False)
        parser.add_argument(
            '-o', '--output', help='output folder path', required=False)
        parser.add_argument(
            '-x', '--proxy', help='proxy to use', required=False)
        parser.add_argument(
            '-usr', '--user', help='username to login', required=False)
        parser.add_argument(
            '-pwd', '--password', help='password to login', required=False)
        parser.add_argument(
            '-w', '--wait_time', help='wait time (in second) between '
                                      'successive requests', required=False)
        parser.add_argument(
            '-ts', '--topic_start', help='starting topic no.', required=False)
        parser.add_argument(
            '-te', '--topic_end', help='ending topic no.', required=False)
        parser.add_argument(
            '-rs', '--rescan', help='Rescan the broken files and re-download',
            action='store_true')
        parser.add_argument(
            '-up', '--update', help='Scrape new posts',
            action='store_true')
        parser.add_argument(
            '-uo', '--useronly', help='Scrape only users page',
            action='store_true')
        parser.add_argument(
            '-fr', '--firstrun', help='Scrape only URLs',
            action='store_true')
        parser.add_argument(
            '-s', '--start_date', help='Scrape from the given dates', required=False)
        parser.add_argument(
            '-b', '--banlist', help='Scrape the ban list', action='store_true')
        parser.add_argument(
            '-lst', '--list', help='List scrapers', action='store_true')
        parser.add_argument(
            '-ch', '--channel', help='Channel to scrape', required=False)
        parser.add_argument(
            '-k', '--kill', help='Kill after this amount of topic page saved', required=False)
        self.parser = parser

    def get_args(self):
        args = self.parser.parse_args()
        return args._get_kwargs()

    def start(self):
        kwargs = {k: v for k, v in self.get_args()}
        if kwargs.get('parse'):
            from forumparse import Parser
            Parser(kwargs).start()
        elif kwargs.get('scrape'):
            from run_scrapper import Scraper
            Scraper(kwargs).do_scrape()
        else:
            self.parser.print_help()


if __name__ == '__main__':
    Collector().start()
