import os
import json
from base_logger import BaseLogger


class NoScrapeLogger(BaseLogger):
	def __init__(self, name, config=None):
		super().__init__(name, config)
		self.cwd = os.path.join(os.getcwd(), "noscrape_v1")
		self.metadata_path = os.path.join(self.cwd, 'metadata')
		self.create_directory(self.metadata_path)

	def append_json(self, metadata):
		ip = metadata["ip"]
		filename = "%s.json" % ip
		filepath = os.path.join(self.metadata_path, filename)
		if os.path.exists(filepath):
			with open(filepath, 'r') as f:
				existing_json = json.loads(f.read())
				existing_json.append(metadata)

			with open(filepath, 'a') as f:
				f.write(json.dumps(existing_json))

		else:
			with open(filepath, 'a') as f:
				f.write(json.dumps([metadata]))







