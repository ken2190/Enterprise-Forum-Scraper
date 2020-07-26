import urllib.parse
import ssl as SSL

from pymongo import MongoClient
from bson.code import Code
from xml.etree import ElementTree as ET
from .no_scrape_plugin import NoScrapePlugin


class MongoScrape(NoScrapePlugin):

	none_database_fields = ["indexes", "stats"]

	def __init__(self, scrape_type='basic', username=None, password=None, auth_db=None, exclude_indexes=[]):
		self.scrape_type = scrape_type
		self.username = username
		self.password = password
		self.auth_db = auth_db
		super().__init__()
		pass

	# Runs the attack
	def run(self):
		return self.scrape()

	# Filters the results based on the filter file provided
	def filter_results(self, results, keywords):
		for database, collections in results.items():

			# Ignore index and stats
			if database in self.none_database_fields:
				continue

			# Loop collection
			for collection, fields in collections.items():
				valid_results = []
				for field in fields:
					if len(keywords) != 0 and self.grep(field, keywords) is False:
						continue
					else:
						valid_results.append(field)
				results[database][collection] = valid_results
		return results

	# Prints out the parsed results
	def print_results(self, results):
		if len(results) == 0:
			self.logger.debug(
				"No Databases found on " + str(self.target) + ":" + str(self.port))  # Excluding the builtin/defaults
			return

		for database, collections in results.items():

			# Ignore non database result field
			if database in self.none_database_fields:
				continue

			self.logger.info("{Database} " + database)

			if len(collections) == 0:
				self.logger.info("\t" + "No collections found on '" + str(collections) + "'")
				continue

			for table, fields in collections.items():
				self.logger.info("\t" + "{Collection} " + table)

				if self.scrape_type != 'fields':
					continue

				for field in fields:
					self.logger.info("\t\t" + "{Field} " + field)

	# Takes in the results from "run" and returns the xml string to output to file
	def results_to_xml(self, results):
		parent = ET.Element('Target')
		parent.set('host', self.clean(str(self.target)))
		parent.set('port', self.clean(str(self.port)))
		parent.set('dbType', self.clean(str("mongo")))
		parent.set('username', self.clean(str(self.username)))
		parent.set('password', self.clean(str(self.password)))
		parent.set('authDB', self.clean(str(self.auth_db)))

		for database, collections in results.items():
			db_tree = ET.SubElement(parent, 'Database')
			db_tree.set('name', self.clean(database))
			for collection, fields in collections.items():
				t_tree = ET.SubElement(db_tree, 'Collection')
				t_tree.set('name', self.clean(collection))
				for field in fields:
					f_tree = ET.SubElement(t_tree, 'Field')
					f_tree.set('name', self.clean(field))
		mydata = self.prettify_xml(parent)
		return mydata

	def results_to_json(self, results):
		return {
			'host': self.clean(str(self.target)),
			'port': self.clean(str(self.port)),
			'dbType': self.clean(str("mongo")),
			'username': self.clean(str(self.username)),
			'password': self.clean(str(self.password)),
			'indexes': results.get("indexes"),
			"database": {
				key: value for key, value in results.items()
				if key not in ["stats", "indexes"]
			}
		}

	# Connect & Log into the DB. Sets the "self.DBClient"
	def connect(self):
		''' Attempts to "attach" to the Mongo instance by logging in (even anonymously). Attempts without SSL first, and then re-attempts with SSL. Will set self.DBClient to a MongoClient instance upon success'''

		# Build the URI to connect to
		uri = 'mongodb://' + str(self.target) + ':' + str(self.port) + '/'
		if self.username is not None or self.password is not None:
			uri = ('mongodb://%s:%s@' + str(self.target) + ':' + str(self.port) + '/' + str(self.auth_db)) % (urllib.parse.quote_plus(self.username), urllib.parse.quote_plus(self.password))
		self.logger.debug("Attempting to attach to Mongo with URI: " + str(uri))

		# Connect to the URI first basically, then over SSL
		use_ssl = False
		while True:
			try:
				self.DBClient = MongoClient(uri, serverSelectionTimeoutMS = 5000, ssl = use_ssl, ssl_cert_reqs=SSL.CERT_NONE)
				self.DBClient.server_info()
				break
			except Exception as e:
				if str(e).find("connection closed") > -1 :
					if use_ssl:
						self.logger.error("An unexpected error occured while attaching to the Mongo instance on " +
										str(self.target) + ":" + str(self.port) + " - " + str(e))
						return False
					else:
						self.logger.debug("Standard connection to " + str(self.target) + ":" + str(self.port) + " dropped. Re-trying with SSL/TLS")
						use_ssl = True
						continue
				if str(e).lower().find("requires authentication") > -1:
					self.logger.error("Authentication required to attach to the Mongo instance on" + str(self.target) + ":" + str(self.port))
					return False
				if str(e).lower().find("authentication failed") > -1:
					self.logger.error("Invalid username or password on " + str(self.target) + ":" + str(self.port))
					return False
				self.logger.error("An unexpected error occured while attaching to the Mongo instance on " + str(self.target) + ":" + str(self.port) + " - " + str(e))
				return False

		# We are connected to the DB
		self.logger.info("Attached to " + str(self.target) + ":" + str(self.port))
		return True

	# Safely disconnects from the DB/instance
	def disconnect(self):
		if self.DBClient is not None:
			self.DBClient.close()
		return True

	def scrape(self):
		db_results = {}

		# Get list of all databases
		try:
			databases = self.DBClient.list_database_names()
		except Exception as e:
			if str(e).lower().find("requires authentication") > -1:
				self.logger.error("Authentication required to enumerate databases on " + str(self.target) + ":" + str(self.port))
				return db_results
			if str(e).lower().find("authentication failed") > -1 :
				self.logger.error("Invalid username or password on " + str(self.target) + ":" + str(self.port))
				return db_results
			else:
				self.logger.error("An unexpected error occured while enumerating the databases on " + str(self.target) + ":" + str(self.port) + " - " + str(e))
				return db_results
		self.logger.debug("Enumerating DBs on " + self.target)

		# Omitt the built-in databases
		if 'admin' in databases:
			databases.remove('admin')
		if 'config' in databases:
			databases.remove('config')
		if 'local' in databases:
			databases.remove('local')

		# Get list of all collections, index names (aka tables)
		for db_name in databases:
			db_results[db_name] = {}
			try:
				# If the DB doesn't exist, no error is thrown, but the DB is empty
				db_session = self.DBClient.get_database(db_name)

				tables = db_session.list_collection_names()

				for collection in tables:
					db_results[db_name][collection] = []

					# Load collection session
					csession = db_session.get_collection(collection)

					# Add basic collection data
					stats = db_session.command("collStats", collection)
					db_results["stats"] = {
						"documents": stats.get("count"),
						"total_doc_size": stats.get("size"),
						"avg_doc_size": stats.get("avgObjSize"),
						"pre_allocated_size": stats.get("storageSize")
					}

					# Add fields
					if self.scrape_type in ['fields', 'all'] :
						map_func = Code("function () { for (var key in this) { emit(key, null);} }")
						reduce_func = Code("function(key, stuff) { return null; }")

						results = csession.inline_map_reduce(map_func, reduce_func, full_response=True)

						tmp_array = []
						for item in results['results']:
							tmp_array.append(str(item['_id']))

						db_results[db_name][collection] = tmp_array

					# Add indexes
					if self.scrape_type in ['index', 'all']:
						db_results["indexes"] = []
						for index in csession.list_indexes():
							is_exclude = False
							for exclude_keyword in self.exclude_indexes:
								if exclude_keyword.lower() in index.get("name").lower():
									is_exclude = True
									break
							if not is_exclude:
								db_results["indexes"].append(
									self.process_index(stats, index)
								)

			except Exception as e:
				self.logger.error("An unexpected error occured on " + self.target + ":" + str(self.port) + " - " + str(e))
				
		return db_results

	def process_index(self, stats, index):
		return {
			"name": index.get("name"),
			"headers": list(index.get("key").items()),
			"size": stats.get("indexSizes").get(index.get("name")),
			"attributes": [
				"%s: %s" % (key, value)
				for key, value in index.items()
				if key not in ["name", "key"]
			]
		}
