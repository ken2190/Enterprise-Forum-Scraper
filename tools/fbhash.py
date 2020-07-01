
import hmac, base64, json, argparse, sys, os
from collections import OrderedDict

from settings import DATASET_HASH_KEY


argument_parser = argparse.ArgumentParser(description="FBHASH arguments")
argument_parser.add_argument('-of', '--out_file', help="Enter out file for hashed dataset")
argument_parser.add_argument('-od', '--out_dir', help="Enter directory for hashed dataset")
argument_parser.add_argument('-if', '--input_file', help="Enter directory for hashed dataset")
argument_parser.add_argument('-id', '--input_dir', help="Enter directory for hashed dataset")


def keyed_hashing_algorithm(value):
    if value is None:
        return value

    value_string = str(value).lower().strip()
    value_bytes = value_string.encode('utf-8', errors='surrogatepass')
    hash_bytes = hmac.digest(DATASET_HASH_KEY.encode('utf-8'), value_bytes, 'sha256')
    hash_string = base64.standard_b64encode(hash_bytes).decode('utf-8')
    return hash_string


def hash_dataset(payload_1):
    for k, v in payload_1.items():
        if isinstance(v, dict):
            payload_1[k] = hash_dataset(payload_1.get(k, {}))
        elif isinstance(v, list):
            payload_1[k] = [keyed_hashing_algorithm(val) for val in v]
        else:
            payload_1[k] = keyed_hashing_algorithm(v)
    return payload_1


def read_input_file(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.loads(f.read())
    except:
        argument_parser.error("Cannot read file: %s" % filepath)
        exit(1)

def write_output_file(filepath, hashed_dataset):
    try:
        with open(filepath, 'w') as f:
            json.dump(hashed_dataset, f)
    except:
        argument_parser.error("Cannot write file: %s" % filepath)
        exit(1)

def hash_datasets_from_input_dir(input_folder):
    hashed_datasets = {}
    try:
        all_files = os.listdir(input_folder)
        for f in all_files:
            absolute_filepath = os.path.join(input_folder, f)
            file_json = read_input_file(absolute_filepath)
            hashed_json = hash_dataset(file_json)
            hashed_datasets[f] = hashed_json

        return hashed_datasets

    except Exception as e:
        argument_parser.error("Error reading files from: %s" % input_folder)
        exit(1)

def write_datasets_to_out_dir(out_dir, hashed_datasets):
    try:
        for k, v in hashed_datasets.items():
            file_path = os.path.join(out_dir, k)
            with open(file_path, 'w') as f:
                json.dump(v, f)
    except Exception as e:
        argument_parser.error("Error writing hashed datasets to directory %s" % out_dir)
        exit(1)
        
if __name__ == '__main__':
    known_args, _ = argument_parser.parse_known_args()
    args = {k: v for k, v in known_args._get_kwargs()}
    input_file = args.get("input_file")
    input_dir = args.get("input_dir")
    out_dir = args.get("out_dir")
    out_file = args.get("out_file")

    if input_file and out_file:
        dataset = read_input_file(input_file)
        hashed_dataset = hash_dataset(dataset)
        write_output_file(out_file, hashed_dataset)

    elif input_dir and out_dir:
        hashed_datasets = hash_datasets_from_input_dir(input_dir)
        write_datasets_to_out_dir(out_dir, hashed_datasets)
        # for k, v in hashed_datasets.items():
        #     # print(k, v)

    else:
        argument_parser.error("Please enter one of the following combinations. Input file and Ouput File, or Input directory and Output Directory")


