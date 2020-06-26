import os
import json
from base_logger import BaseLogger


class NoScrapeLogger(BaseLogger):
	def __init__(self, name, config=None):
		super().__init__(name, config)
		self.cwd = os.path.join(os.getcwd(), "noscrape_v1")
		self.metadata_path = os.path.join(self.cwd, 'metadata')
		self.create_directory(self.metadata_path)

	def read_json(self, filepath):
		with open(filepath, 'r') as f:
			return json.loads(f.read())

	def write_json(self, metadata, out_folder=None):
		ip = metadata["_source"]["ip"]
		filename = "%s.json" % ip
		filepath = os.path.join(out_folder, filename) if out_folder else os.path.join(self.metadata_path, filename)
		with open(filepath, 'w') as ip_json:
			json.dump(metadata, ip_json)

	def append_json(self, metadata):
		ip = metadata["ip"]
		filename = "%s.json" % ip
		filepath = os.path.join(self.metadata_path, filename)
		if os.path.exists(filepath):
			existing_json = self.read_json(filepath)
			existing_json.append(metadata)
			with open(filepath, 'w') as f:
				json.dump(existing_json, f)

		else:
			with open(filepath, 'w') as f:
				json.dump([metadata], f)



