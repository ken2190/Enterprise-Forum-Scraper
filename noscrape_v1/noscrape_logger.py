import os
from base_logger import BaseLogger


class NoScrapeLogger(BaseLogger):
	def __init__(self, name, config=None):
		super().__init__(name, config)
		self.cwd = os.path.join(os.getcwd(), "noscrape_v1")
		self.metadata_path = os.path.join(self.cwd, 'metadata')
		self.create_directory(self.metadata_path)







