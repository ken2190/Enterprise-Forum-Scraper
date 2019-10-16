import argparse
import os
from glob import glob
from scraper import SCRAPER_MAP

UPDATE_DB_PATH = '/Users/PathakUmesh/forums.db'


class Scraper:
    def __init__(self, kwargs):
        self.counter = 1
        self.kwargs = kwargs

    def do_scrape(self):
        if self.kwargs.get('list'):
            print('Following scrapers are available')
            for index, scraper in enumerate(SCRAPER_MAP.keys(), 1):
                print(f'{index}. {scraper}')
            return
        template = self.kwargs.get('template')
        if not template:
            print('template (-t/--template) missing')
            return
        scraper = SCRAPER_MAP.get(template.lower())
        if not scraper:
            print('Message: your target name is wrong..!')
            return
        output_folder = self.kwargs.get('output')
        if not output_folder:
            print('Output path missing')
            return
        self.kwargs.update({'db_path': UPDATE_DB_PATH})
        # ------------make folder if not exist -----------------
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        scraper_obj = scraper(self.kwargs)
        if self.kwargs.get('rescan'):
            scraper_obj.do_rescan()
        # elif kwargs.get('update'):
        #     scraper_obj.do_new_posts_scrape()
        else:
            scraper_obj.do_scrape()


def main():
    Scraper().do_scrape()


if __name__ == '__main__':
    main()
