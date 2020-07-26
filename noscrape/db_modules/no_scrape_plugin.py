import logging
import socket
import re
from xml.etree import ElementTree as ET
from xml.dom import minidom


class NoScrapePlugin:
    def __init__(self):
        logging.basicConfig(level = logging.INFO, format='[%(asctime)s] %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
        self.logger = logging.getLogger(__name__)
        self.DBClient = None
        self.timeout = 5
        self.target = ""
        self.port = -1

    def clean(self, data):
        try:
            return data.encode('utf-8', errors='ignore').decode("utf-8")
        except Exception as e:
            self.logger.error("Error cleaning data for: " + str(data))
            return data

    def grep(self, data, list_data):
        data = str(data).lower()
        for key in list_data:
            if bool(re.search(".*" + key + ".*", data)):
                return True
        return False

    def prettify_xml(self, elem):
        """Return a pretty-printed XML string for the Element."""
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="\t")

    def set_target(self, targetIP, port):
        self.target = targetIP
        self.port = port

    def test_connection(self):
        ''' Simply tries to connect out to the port on TCP '''
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.timeout)
            s.connect((self.target, self.port))
            s.close()
        except Exception as e:
            self.logger.error("Error connecting to " + str(self.target) + ":" + str(self.port) + " - " + str(e))
            return False
        else:
            self.logger.debug("Connected to " + str(self.target) + ":" + str(self.port))
            return True

    def connect(self):
        raise Exception("[noScrapePlugin]::connect function needs to be overridden!")
        pass

    def disconnect(self):
        raise Exception("[noScrapePlugin]::disconnect function needs to be overridden!")
        pass

    def basic(self):
        raise Exception("[noScrapePlugin]::basic function needs to be overridden!")
        pass

    def fields(self):
        raise Exception("[noScrapePlugin]::fields function needs to be overridden!")
        pass
