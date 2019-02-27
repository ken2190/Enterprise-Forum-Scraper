import argparse
import os
from glob import glob
from scraper.antichat import AntichatScrapper
from scraper.breachforums import BreachForumsScrapper
from scraper.exploit import ExploitScrapper
from scraper.exploit_private import ExploitPrivateScrapper
from scraper.lolzteam import LolzScrapper
from scraper.verified import VerifiedScrapper
from scraper.sentryMBA import SentryMBAScrapper
from scraper.bitcointalk import BitCoinTalkScrapper
from scraper.psbdmp import PasteBinScrapper
from scraper.wallstreet import WallStreetScrapper
from scraper.kickass import KickAssScrapper
from scraper.galaxy3 import Galaxy3Scrapper
from scraper.badkarma import BadKarmaScrapper
from scraper.antichat_v2 import Antichatv2Scrapper
from scraper.sinister import SinisterScrapper
from scraper.sentryMBA_v2 import SentryMBAv2Scrapper
from scraper.verified_carder import VerifiedCarderScrapper
from scraper.carder import CarderScrapper
from scraper.ccc_mn import CCCMNScrapper
from scraper.cracked_to import CrackedToScrapper
from scraper.sky_fraud import SkyFraudScrapper
from scraper.nulled import NulledScrapper
from scraper.dark_skies import DarkSkiesScrapper

SCRAPER_MAP = {
    'antichat': AntichatScrapper,
    'breachforums': BreachForumsScrapper,
    'exploit': ExploitScrapper,
    'exploitprivate': ExploitPrivateScrapper,
    'lolzteam': LolzScrapper,
    'verified': VerifiedScrapper,
    'verified1': VerifiedScrapper,
    'sentrymba': SentryMBAScrapper,
    'bitcointalk': BitCoinTalkScrapper,
    'psbdmp': PasteBinScrapper,
    'wallstreet': WallStreetScrapper,
    'kickass': KickAssScrapper,
    'galaxy3': Galaxy3Scrapper,
    'badkarma': BadKarmaScrapper,
    'antichat_v2': Antichatv2Scrapper,
    'sinister': SinisterScrapper,
    'sentrymba_v2': SentryMBAv2Scrapper,
    'verified_carder': VerifiedCarderScrapper,
    'carder': CarderScrapper,
    'ccc_mn': CCCMNScrapper,
    'cracked_to': CrackedToScrapper,
    'sky_fraud': SkyFraudScrapper,
    'nulled': NulledScrapper,
    'dark_skies': DarkSkiesScrapper,
}


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
