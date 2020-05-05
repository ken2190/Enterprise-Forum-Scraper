
# S3 Libraries
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from .NoScrapePlugin import NoScrapePlugin
from xml.etree import ElementTree as ET


class S3BruteForce(NoScrapePlugin):
	def __init__(self, aws_access_key_id, aws_secret_access_key, hitlist):
		self.aws_access_key_id 		= aws_access_key_id
		self.aws_secret_access_key 	= aws_secret_access_key
		self.hitlist 				= hitlist
		self.AWSClient 				= None
		super().__init__()

	def connect(self):
		# S3 Connect
		try:
			self.AWSClient = boto3.resource('s3', aws_access_key_id = self.aws_access_key_id, aws_secret_access_key = self.aws_secret_access_key, config=Config(signature_version='s3v4'))
		except Exception as e:
			return False
		return True

	def runAttack(self, outFile = None):
		for line in open(self.hitlist, "r"):
			line = line.replace("\n", "").replace("\x00", "").replace("\r", "").replace("\b", "")
			if(len(line) == 0):
				continue
			try:
				self.AWSClient.meta.client.head_bucket(Bucket=line)
			except ClientError as e:
				# Exists but no access
				if int(e.response['Error']['Code']) == 403:
					self.logger.debug("[S3_NoAccess] 's3://" + line + "' exists, but we do not have access")
					continue
				if int(e.response['Error']['Code']) == 404:
					self.logger.debug("[S3_DoesNotExist] 's3://" + line + "' does not exist")
					continue 
			self.logger.info("Identified access to 's3://" + str(line) + "' - Listing all objects/files...")
			bucket = self.AWSClient.Bucket(line)
			parent = ET.Element('S3Bucket')
			parent.set('url', 's3://' + line)
			for item in bucket.objects.all():
				print("\t" + str(item.__dict__['_key']))
				fdata = ET.SubElement(parent, 'File')
				fdata.set('name', str(item.__dict__['_key']))
			self.logger.info("...completed")

			mydata = self.prettify_xml(parent)
			if not firstWrite:
				# Remove the XML declaration
				mydata = '\n'.join(mydata.split("\n")[1:])

			if outFile != None:
				myfile = open(outFile, "a")
				myfile.write(mydata)
				myfile.close()
				firstWrite = False
		self.logger.info("S3 Module Completed")