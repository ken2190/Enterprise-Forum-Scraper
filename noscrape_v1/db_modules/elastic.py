
from datetime import datetime
from elasticsearch import Elasticsearch
from base_logger import BaseLogger
from urllib3.exceptions import ConnectTimeoutError
import socket

class Elastic:
	def __init__(self, scrape_type=None, ip=None, port=None, limit=None, keywords=None, exclude_indexes=[]):
		self.scrape_type = scrape_type
		self.limit = limit
		self.keywords = keywords
		self.exclude_indexes = exclude_indexes
		self.logger = BaseLogger(__name__, None)
		self.ip = ip
		self.port = int(port)
		self.timeout = 5

	def connect(self):
		try:
			return Elasticsearch(hosts=[{"host": self.ip, "port": self.port}])
		except Exception as e:
			return False

	def test_connection(self):
		''' Simply tries to connect out to the port on TCP '''
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.settimeout(self.timeout)
			s.connect((self.ip, self.port))
			s.close()
			return True
		except Exception as e:
			self.logger.error("Error connecting to " + str(self.ip) + ":" + str(self.port) + " - " + str(e))
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

	def get_index_count(self, indexes):
		indexes_count = {}
		for index in indexes:
			index_name = index['index']
			index_record_count = index['docs.count']
			indexes_count[index_name] = index_record_count
		return indexes_count

	# get index names and count of each index
	def get_index_names(self, indexes):
		return [index["index"] for index in indexes]

	def fetch_metadata(self, db_type):
		try:
			# self.logger.info("----Requesting for cross-section of each index for {}:{}".format(self.ip, self.port))
			connection_verified = self.test_connection()
			if connection_verified:
				elastic_db = self.connect()
				if elastic_db:
					indexes = elastic_db.cat.indices(v=True, format='json')
					index_names = self.get_index_names(indexes)
					indexes_count = self.get_index_count(indexes)
					index_headers = list(indexes[0].keys())
					json_to_store = {
						"index_names": index_names,
						"index_headers": index_headers,
						"indexes_count": indexes_count,
						"ip": self.ip,
						"port": self.port,
						"database_type": db_type,
						"date": str(datetime.now())
					}
					# self.logger.info("----Results: {}:{}".format(self.ip, self.port))
					elastic_db.close()
					return json_to_store

			return False

		except Exception as e:
			print(str(e))
			return False

	def dump(self):
		pass
