

from elasticsearch import Elasticsearch
from base_logger import BaseLogger
from urllib3.exceptions import ConnectTimeoutError

class Elastic:
	def __init__(self, scrape_type=None, ip=None, port=None, limit=None, keywords=None, exclude_indexes=[]):
		self.scrape_type = scrape_type
		self.limit = limit
		self.keywords = keywords
		self.exclude_indexes = exclude_indexes
		self.logger = BaseLogger(__name__, None)
		self.ip = ip
		self.port = port

	def connect(self):
		try:
			return Elasticsearch(hosts=[{"host": self.ip, "port": self.port}])
		except Exception as e:
			return False

	def get_index_names(self, db):
		self.logger.info("----Requesting for cross-section of each index for {}:{}".format(self.ip, self.port))
		indexes = db.cat.indices(v=True, format='json')
		index_names = list(indexes[0].keys())
		return index_names

	def fetch_metadata(self):
		try:
			elastic_db = self.connect()
			if elastic_db:
				index_names = self.get_index_names(elastic_db)
				
				# self.logger.info("----Results: {}:{}".format(self.ip, self.port))
				# elastic_db.close()
				# return results

		except Exception as e:
			pass

	def dump(self):
		pass
