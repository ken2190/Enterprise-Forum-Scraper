import json
import traceback
import argparse
import re
import paramiko
import os
import stat
from zipfile import ZipFile

class ShadownetScrapper:
    def __init__(self, kwargs):
        self.args = kwargs

    def getSSHClient(self, SSHConfig):
        print(f'Connecting {SSHConfig["host"]}...')
        ssh = paramiko.SSHClient()

        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(SSHConfig['host'], username=SSHConfig['username'], password=SSHConfig['password'])
            ssh.get_transport().window_size = 10000000
        except Exception as e:
            print(f'ERROR Can not connect to {SSHConfig["host"]}.')
            print(e)
            return None
        print(f'Connected to {SSHConfig["host"]}')
        return ssh

    def downloadSSHFile(self, ssh, remotepath, localpath):
        try:
            ftp_client=ssh.open_sftp()
            ftp_client.get(remotepath, localpath)
            ftp_client.close()
        except Exception as e:
            print(f'ERROR Cannot download file - {remotepath}')
            print(e)
            return False
        print(f'Download file - {remotepath}')
        return True

    def sftp_exists(self, sftp, path):
        try:
            sftp.stat(path)
            return True
        except FileNotFoundError:
            return False

    def is_dir_exists(self, path):
        return os.path.exists(path) and os.path.isdir(path)

    def zip_download(self, ssh, folder_path, output_path):
        """ Zip Folder and Download"""
        input_folder_name = folder_path.split("/")[-1]
        output_file = os.path.join('/tmp', input_folder_name) + '.zip'

        try:
            print(f'Zipping {folder_path} ...')
            stdin, stdout, stderr = ssh.exec_command(f'cd {folder_path} && zip -r {output_file} .')
            if not stdout.readlines():
                return False
        except Exception as e:
            print(e)
            return False
        
        ftp_client = ssh.open_sftp()
        filename = input_folder_name + '.zip'
        ftp_client.get(output_file, os.path.join(output_path, filename))
        print(f'Download done to local: {os.path.join(output_path, filename)}')
        stdin, stdout, stderr = ssh.exec_command(f'rm -rf {output_file}')

        return os.path.join(output_path, filename)

    def download_logs(self, ssh, input_path, output_path):
        """ Download logs from server to local dir"""
        ftp_client = ssh.open_sftp()

        if not self.sftp_exists(ftp_client, input_path):
            err_msg = "ERROR : Input directory does not exist: %s" % input_path
            print(err_msg)
            exit(2, RuntimeError(err_msg))
        
        folder_name = input_path.split("/")[-1]
        local_dir = os.path.join(output_path, folder_name)

        if not self.is_dir_exists(local_dir):
            os.makedirs(local_dir)
            
        for filename in ftp_client.listdir(input_path):
            if stat.S_ISDIR(ftp_client.stat(os.path.join(input_path, filename)).st_mode):
                self.download_logs(ssh, os.path.join(input_path, filename), os.path.join(local_dir, filename))
            else:
                if not os.path.isfile(os.path.join(local_dir, filename)):
                    ftp_client.get(os.path.join(input_path, filename), os.path.join(local_dir, filename))
                    print(f'Download done : {os.path.join(input_path, filename)}')

    def process(self):
        SSHConfig={
            'host': self.args["server"],
            'username': self.args["user"],
            'password': self.args["password"],
        }

        input_path = self.args["input_path"]
        output_path = self.args["output"]

        # Connect to server
        ssh = self.getSSHClient(SSHConfig)

        # Download Logs
        print("="*100)
        self.download_logs(ssh, input_path, output_path)
        # download_path = self.zip_download(ssh, input_path, output_path)
        # if download_path:
        #     with ZipFile(download_path, 'r') as zipObj:
        #         print("="*100)
        #         print(f'Unzipping to {download_path.strip(".zip")}')
        #         zipObj.extractall(download_path.strip(".zip"))
        #         os.remove(download_path)
    
    def start(self):
        self.process()