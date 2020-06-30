from fbhash import hash_dataset
from fbhash_test_data import dataset_2
import json
from copy import deepcopy

dataset_2_copy = deepcopy(dataset_2)
encrypted_dataset = hash_dataset(dataset_2_copy)

print(json.dumps(encrypted_dataset, indent=4))
print("\n\n")
print(json.dumps(dataset_2, indent=4))
