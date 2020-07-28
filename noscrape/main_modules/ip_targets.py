from netaddr import IPNetwork
import logging


class IpTargets:
	def __init__(self, file_path=None, cidr=None, port=None):
		logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
		self.logger = logging.getLogger(__name__)

		self.targetList = [] 	# Each item is a tuple of (IPNetwork, port)

		if cidr is not None and port is None:
			raise Exception("Port is missing")
		if cidr is None and port is not None:
			raise Exception("IP/CIDR is missing from input")

		if cidr is not None and port is not None:
			self.load_from_input(cidr, port)
		if file_path is not None:
			self.load_from_file(file_path)

	def find_delimeter(self, first_line):
		delimeter_options = [',', ':', '|']
		for delimeter_option in delimeter_options:
			if delimeter_option in first_line:
				return delimeter_option
		return None

	def load_from_file(self, file_path):
		try:
			file_handle = open(file_path, "r")
			first_line = file_handle.readline()
			delimeter = self.find_delimeter(first_line)
			file_handle.close()
		except Exception as e:
			raise Exception("Error when trying to open '" + file_path + "' - " + str(e))

		if delimeter is None:
			raise Exception("CSV delimeter of input file should be one of: [',', ':', '|']")

		file_handle = open(file_path, "r")

		for line in file_handle:
			line = line.replace("\n", "").replace("\x00", "").replace("\r", "").replace("\b", "").replace(" ", "")
			try:
				ip, port = line.split(delimeter)
				port = int(port)
				net = IPNetwork(ip)
				self.targetList.append((net, port))
				self.logger.debug("Added [" + str(net) + " Port: " + str(port) + "] to targets")
			except Exception as e:
				self.logger.error("Error while parsing '" + file_path + "' - " + str(e))

	def load_from_input(self, ip_string, port_string):
		port = int(port_string)
		net = IPNetwork(ip_string)
		self.targetList.append((net, port))
		self.logger.debug("Added [" + str(net) + " Port: " + str(port) + "] to targets")

	def __iter__(self):
		return iter(self.targetList)


