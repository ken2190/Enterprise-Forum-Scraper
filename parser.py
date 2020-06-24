from argparse import ArgumentParser


class Parser:

	def __init__(self, description=None, arguments=[]):
		self.parser = ArgumentParser(description=description)
		self.set_args(arguments)

	def set_args(self, arguments):
		for argument in arguments:
			self.parser.add_argument(*argument["args"], **argument["kwargs"])

	def get_args(self):
		args, _ = self.parser.parse_known_args()
		cli_args = args._get_kwargs()
		return {k: v for k, v in cli_args}

	def print_help(self):
		self.parser.print_help()

	def error(self, msg):
		self.parser.error(msg)

