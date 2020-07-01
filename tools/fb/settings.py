from dotenv import load_dotenv
import os
load_dotenv()

DATASET_HASH_KEY = os.getenv('DATASET_HASH_KEY') or 'facebook,instagram,oculus,whatsapp'

