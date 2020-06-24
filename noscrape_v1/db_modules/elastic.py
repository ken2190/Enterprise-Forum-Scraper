

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

	# get index names and count of each index
	def get_index_names(self, db):
		indexes_count = {}
		self.logger.info("----Requesting for cross-section of each index for {}:{}".format(self.ip, self.port))
		indexes = db.cat.indices(v=True, format='json')
		for index in indexes:
			index_name = index['index']
			index_record_count = index['docs.count']
			indexes_count[index_name] = index_record_count
		index_names = list(indexes[0].keys())
		return index_names, indexes_count

	def fetch_metadata(self):
		try:
			elastic_db = self.connect()
			if elastic_db:
				index_names, indexes_count = self.get_index_names(elastic_db)
				print(index_names)
				print(indexes_count)
				# self.logger.info("----Results: {}:{}".format(self.ip, self.port))
				elastic_db.close()
				# return results

		except Exception as e:
			print(str(e))
			pass

	def dump(self):
		pass
