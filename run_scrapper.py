import argparse
import os
from glob import glob
from scraper import SCRAPER_MAP


class Scraper:
    def __init__(self):
        self.counter = 1

    def get_args(self):
        parser = argparse.ArgumentParser(
            description='Scrapping Forums Framework')
        parser.add_argument(
            '-t', '--template', help='Template forum to scrape', required=True)
        parser.add_argument(
            '-o', '--output', help='output folder path', required=True)
        parser.add_argument(
            '-x', '--proxy', help='proxy to use', required=False)
        parser.add_argument(
            '-u', '--user', help='username to login', required=False)
        parser.add_argument(
            '-p', '--password', help='password to login', required=False)
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
            '-d', '--daily', help='Scrape new posts for today',
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
        args = parser.parse_args()
        return args._get_kwargs()
        # return args.template, args.output, args.proxy, args.user, args.password

    def do_scrape(self):
        kwargs = {k: v for k, v in self.get_args()}
        output_folder = kwargs.get('output')

        # ------------make folder if not exist -----------------
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        template = kwargs.get('template')
        scraper = SCRAPER_MAP.get(template.lower())
        if not scraper:
            print('Message: your target name is wrong..!')
            return
        scraper_obj = scraper(kwargs)
        if kwargs.get('rescan'):
            scraper_obj.do_rescan()
        elif kwargs.get('daily'):
            scraper_obj.do_new_posts_scrape()
        else:
            scraper_obj.do_scrape()


def main():
    Scraper().do_scrape()


if __name__ == '__main__':
    main()
