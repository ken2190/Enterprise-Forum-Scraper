import os, random 
import json
import sys
import argparse
import subprocess


class Parser:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            '-i', '--input', help='Input File', required=True)
        self.parser.add_argument(
            '-o', '--output', help='Output File', required=True)

    def get_args(self,):
        return self.parser.parse_args()

date_mapping = {
	"01": 31,
	"02": 28,
	"03": 31,
	"04": 30,
	"05": 31,
	"06": 30,
	"07": 31,
	"08": 31,
	"09": 30,
	"10": 31,
	"11": 30,
	"12": 31,
}

def main():
	args = Parser().get_args()
	input_file = args.input
	output_file = args.output

	with open(output_file, mode='w') as out_file:
		with open(input_file, 'r') as in_file:
			for line_number, line in enumerate(in_file, 1):
				item = json.loads(line)
				dob = item['dob']

				year = dob.split("-")[0]
				month = dob.split("-")[1]
				day = dob.split("-")[2]
				if month == '00':
					month = str(random.randint(1, 12)).zfill(2) 

				if day == '00':
					day = str(random.randint(1, date_mapping[month])).zfill(2)

				dob = f"{year}-{month}-{day}"
				item['dob'] = dob

				out_file.write(json.dumps(item))
				out_file.write("\n")
				print(f"Processed line: {line_number}")

if __name__ == '__main__':
	main()
