from fbhash import hash_dataset
from fbhash_test_data import dataset_2
import json

encrypted_dataset = hash_dataset(dataset_2, dataset_2)
print(json.dumps(encrypted_dataset, indent=4))
