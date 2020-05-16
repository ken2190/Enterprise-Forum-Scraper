import argparse
import os
from glob import glob
from scraper import SCRAPER_MAP

UPDATE_DB_PATH = '/Users/PathakUmesh/forums.db'


class Scraper:
    def __init__(self, kwargs):
        self.counter = 1
        self.kwargs = kwargs

    def is_blank(self):
        values = [
            value for value in self.kwargs.values()
            if value
        ]
        return len(values) == 0

    def print_list_template(self):
        print('Following scrapers are available')
        for index, scraper in enumerate(SCRAPER_MAP.keys(), 1):
            print(f'{index}. {scraper}')

    def do_scrape(self):
        if self.is_blank():
            print(
                "Require parameter:\n"
                "- -t/--template: template name\n"
                "- -o/--output: output folder"
            )
            return

        if self.kwargs.get('list'):
            self.print_list_template()
            return

        template = self.kwargs.get('template')

        if not template:
            help_message = """
            Usage: collector.py -scrape [-t TEMPLATE] [-o OUTPUT] [-s START_DATE]\n
            Arguments:
            -t | --template TEMPLATE:     Template forum to scrape
            -o | --output OUTPUT:         Output folder path

            Optional:
            -s | --start_date START_DATE: Scrape threads that are newer than supplied date
            -l | --list:                  List available parsers (tempalte namess)

            """
            print(help_message)
            return

        scraper = SCRAPER_MAP.get(template.lower())
        if not scraper:
            print('Not found template!')
            self.print_list_template()
            return

        output_folder = self.kwargs.get('output')
        if not output_folder:
            print('Output path missing')
            return

        # ------------make folder if not exist -----------------
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        scraper_obj = scraper(self.kwargs)
        if self.kwargs.get('rescan'):
            scraper_obj.do_rescan()
        elif self.kwargs.get("start_date"):
            try:
                scraper_obj.do_scrape_from_date()
            except Exception as err:
                print(
                    "Error running do scrape from date: %s" % err
                )
                scraper_obj.do_scrape()
        else:
            scraper_obj.do_scrape()


def main():
    Scraper().do_scrape()


if __name__ == '__main__':
    main()
