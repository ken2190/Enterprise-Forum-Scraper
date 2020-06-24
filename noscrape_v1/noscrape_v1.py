from .noscrape_logger import NoScrapeLogger
from .config import noscrape_parser_arguments

from parser import Parser
import argparse


class NoScrapeV1:
    def __init__(self, args):
        self.logger = NoScrapeLogger(__name__)
        self.parser = Parser(description="Noscrape parsing tool", arguments=noscrape_parser_arguments)
        self.args = args

    def verify_args(self):
        noscrape_args = self.parser.get_args()
        return noscrape_args.get('dump') or noscrape_args.get("meta")

    def run(self):
        valid_args = self.verify_args()
        if valid_args:
            print("[+] Args are valid, processing args")
        else:
            self.parser.error('--either -d/--dump or -m/--meta is required')

    def run_es(self):
        print("Running es")




