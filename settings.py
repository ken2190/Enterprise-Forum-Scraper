from dotenv import load_dotenv
import os
load_dotenv()

DV_BASE_URL = os.getenv('DV_BASE_URL') or 'https://api.dataviper.io'
API_TOKEN = os.getenv('API_TOKEN')
OUTPUT_DIR = os.getenv('OUTPUT_DIR') or 'output'
PARSE_DIR = os.getenv('PARSE_DIR') or 'parse'
LOG_DIR = os.getenv('LOG_DIR') or 'log'
PYTHON_BIN = os.getenv('PYTHON_BIN') or 'python'
