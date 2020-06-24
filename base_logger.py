import logging, os
from config import default_logging_config


class BaseLogger:

	def __init__(self, name, config):
		self.config = config or default_logging_config
		logging.basicConfig(**self.config)
		self.logger = logging.getLogger(name)

	def log(self, msg):
		self.logger.log(msg)

	def info(self, msg):
		self.logger.info(msg)

	def append(self, filename, lines):
		with open(filename, 'a') as f:
			f.writelines(lines)

	def create_directory(self, path):
		if os.path.exists(path):
			return
		else:
			os.makedirs(path)