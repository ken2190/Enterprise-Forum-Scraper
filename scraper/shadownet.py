import json
import traceback
import argparse
import re
import paramiko
import os
import stat
from zipfile import ZipFile
import dateutil.parser as dparser
from datetime import datetime

USERNAME='ejabberd'
KEY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ssl_certificate/shadow.pem')
INPUT_PATH='/data/log/ejabberd'

class ShadownetScrapper:
    def __init__(self, kwargs):
        self.host = kwargs['sitename']
        self.username = USERNAME
        self.key_file = KEY_FILE
        self.input_path = INPUT_PATH
        self.output_path = kwargs['output']
        self.start_date = kwargs['start_date']
        self.time_format = "%Y-%m-%d"
        self.sitename = kwargs["sitename"]

        help_message = """
            Usage: collector.py -scrape [-t TEMPLATE] [-o OUTPUT] [--sitename SITENAME] [-s START_DATE]\n
            Arguments:
            -t          | --template TEMPLATE:     Template forum to scrape
            -o          | --output OUTPUT:         Output folder path
            --sitename                             Sitename

            Optional:
            --start_date                           START_DATE: Scrape threads that are newer than supplied date
            """

        if not self.sitename or not self.output_path:
            print(help_message)
            exit(1)

        if self.start_date:
            try:
                self.start_date = datetime.strptime(
                    self.start_date,
                    self.time_format
                )
            except Exception as err:
                raise ValueError(
                    "Wrong date format. Correct format is: %s. Detail: %s" % (
                        self.time_format,
                        err
                    )
                )

    def getSSHClient_key(self, SSHConfig):
        print(f'Connecting {SSHConfig["host"]}...')
        ssh = paramiko.SSHClient()

        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(SSHConfig['host'], username=SSHConfig['username'], key_filename=SSHConfig['key_file'])
            ssh.get_transport().window_size = 10000000
        except Exception as e:
            print(f'ERROR Can not connect to {SSHConfig["host"]}.')
            print(e)
            exit(1)
        print(f'Connected to {SSHConfig["host"]}')
        return ssh

    def sftp_exists(self, sftp, path):
        try:
            sftp.chdir(path)
            return True
        except FileNotFoundError:
            return False

    def is_dir_exists(self, path):
        return os.path.exists(path) and os.path.isdir(path)

    def download_dir(self, ssh, input_path, output_path):
        """Download Directory"""
        ftp_client = ssh.open_sftp()

        if not self.sftp_exists(ftp_client, input_path):
            err_msg = "ERROR : Input directory does not exist: %s" % input_path
            print(err_msg)
            exit(1)
        
        local_dir = output_path

        if not self.is_dir_exists(local_dir):
            os.makedirs(local_dir)
        
        if not ftp_client.listdir(input_path):
            err_msg = "Warning : No log file at directory: %s" % input_path
            print(err_msg)
            exit(1)

        for filename in ftp_client.listdir(input_path):
            if not os.path.isfile(os.path.join(local_dir, filename)):
                ftp_client.get(os.path.join(input_path, filename), os.path.join(local_dir, filename))
                print(f'Done : {os.path.join(input_path, filename)}')
            else:
                print(f'Already Exist : {os.path.join(input_path, filename)}')

    def download_logs(self, ssh, input_path, output_path):
        """ Download logs from server to local dir"""
        ftp_client = ssh.open_sftp()

        if not self.sftp_exists(ftp_client, input_path):
            err_msg = "ERROR : Input directory does not exist: %s" % input_path
            print(err_msg)
            exit(1)
        
        local_dir = output_path
        if not self.is_dir_exists(local_dir):
            os.makedirs(local_dir)
        
        domain_dir_list = sorted(ftp_client.listdir(input_path))
        if not domain_dir_list:
            err_msg = "Warning : Input directory %s is empty" % input_path
            print(err_msg)
            exit(1)
            
        for domain_dir_name in domain_dir_list:
            local_dir = output_path

            domain_dir_path = os.path.join(input_path, domain_dir_name)
            if stat.S_ISDIR(ftp_client.stat(domain_dir_path).st_mode):
                print("="*100)
                print(f"Downloading logs for {domain_dir_path}")
                
                daily_dir_list = sorted(ftp_client.listdir(domain_dir_path))
                if not daily_dir_list:
                    err_msg = f'Warning : Log directory for {domain_dir_name} is empty. Dir Path: {domain_dir_path}\n'
                    print(err_msg)
                    continue
                
                local_dir = os.path.join(local_dir, domain_dir_name)
                for daily_dir_name in daily_dir_list:
                    _dir = daily_dir_name.lstrip("log_")
                    try:
                        ts = dparser.parse(_dir)
                    except ValueError:
                        continue
                    
                    if self.start_date:
                        if ts >= self.start_date:
                            self.download_dir(ssh, os.path.join(domain_dir_path, daily_dir_name), os.path.join(local_dir, daily_dir_name))
                            print("-"*100)
                            print(f"Sub Dir Done: {os.path.join(domain_dir_path, daily_dir_name)} to {os.path.join(local_dir, daily_dir_name)}\n")
                    else:
                        self.download_dir(ssh, os.path.join(domain_dir_path, daily_dir_name), os.path.join(local_dir, daily_dir_name))
                        print("-"*100)
                        print(f"Sub Dir Done: {os.path.join(domain_dir_path, daily_dir_name)} to {os.path.join(local_dir, daily_dir_name)}\n")
            else:
                continue

    def process(self):
        SSHConfig={
            'host': self.host,
            'username': self.username,
            'key_file': self.key_file
        }
        
        # Connect to server
        ssh = self.getSSHClient_key(SSHConfig)

        # Download Logs
        self.download_logs(ssh, self.input_path, self.output_path)
    
    def start(self):
        self.process()
