
import hmac, base64, json
from collections import OrderedDict
TEST_KEY = 'facebook,instagram,oculus,whatsapp'

test_data = {
	"a": 1,
	"b": 2,
	"c": {
		"c1": '1c',
		"c2": '2c',
		"c3": {
			"d": "doit",
			"d1": '1d',
			"d2": '2d'
		},
		"c4": "4c",
		"the_list": [1,2,3,4,5]
	},
	"d": 3,
	"e": 4
}

def keyed_hashing_algorithm(value):
	value_string = str(value).lower().strip()
	value_bytes = value_string.encode('utf-8')
	hash_bytes = hmac.digest(TEST_KEY.encode('utf-8'), value_bytes, 'sha256')
	hash_string = base64.standard_b64encode(hash_bytes).decode('utf-8')
	return hash_string


def hash_dataset(d, u):
	for k, v in u.items():
		if isinstance(v, dict):
			d[k] = hash_dataset(d.get(k, {}), v)
		elif isinstance(v, list):
			d[k] = [keyed_hashing_algorithm(val) for val in v]
		else:
			d[k] = keyed_hashing_algorithm(v)
	return d


doit = hash_dataset(test_data, test_data)
print(json.dumps(doit, indent=4))

