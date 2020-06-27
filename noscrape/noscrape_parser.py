from argparse import ArgumentParser
from .config import noscrape_parser_arguments


class NoScrapeParser(ArgumentParser):

	def __init__(self, description=None):
		super().__init__(description=description or 'NoScrape Parser')

