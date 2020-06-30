
import hmac, base64, json
from collections import OrderedDict

from settings import DATASET_HASH_KEY


def keyed_hashing_algorithm(value):
	if value is None:
		return value

	value_string = str(value).lower().strip()
	value_bytes = value_string.encode('utf-8', errors='surrogatepass')
	hash_bytes = hmac.digest(DATASET_HASH_KEY.encode('utf-8'), value_bytes, 'sha256')
	hash_string = base64.standard_b64encode(hash_bytes).decode('utf-8')
	return hash_string


def hash_dataset(payload_1, payload_2):
	for k, v in payload_2.items():
		if isinstance(v, dict):
			payload_1[k] = hash_dataset(payload_1.get(k, {}), v)
		elif isinstance(v, list):
			payload_1[k] = [keyed_hashing_algorithm(val) for val in v]
		else:
			payload_1[k] = keyed_hashing_algorithm(v)
	return payload_1


