

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

	def get_record_count(self, index_data):
		record_count = 0
		for index_obj in index_data:
			index_count = index_obj.get("docs.count", None)
			if index_count:
				record_count += int(index_count)
			else:
				print("No Index count")

		return record_count

	def get_index_names(self, db):
		index_names, record_count = [], 0
		self.logger.info("----Requesting for cross-section of each index for {}:{}".format(self.ip, self.port))
		indexes = db.cat.indices(v=True, format='json')
		record_count = self.get_record_count(indexes)
		index_names = list(indexes[0].keys())
		return index_names, record_count

	def fetch_metadata(self):
		try:
			elastic_db = self.connect()
			if elastic_db:
				index_names, record_count = self.get_index_names(elastic_db)
				# self.logger.info("----Results: {}:{}".format(self.ip, self.port))
				elastic_db.close()
				# return results

		except Exception as e:
			print(str(e))
			pass

	def dump(self):
		pass
