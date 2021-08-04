import os, random 
import json
import sys
import argparse
import subprocess
import shutil


def remove_ssn(file_name, pos):
	cmd = f'sed -i 1,{pos}d {file_name}'
	subprocess.run(
		cmd,
		shell=True,
	)

	print(f'Done')
	

def get_ssn(file_name, pos, line_size):
	file = open(file_name, 'r')
	file.seek(line_size*pos)
	line = file.readline()
	file.close()

	return line.strip()

class Parser:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            '-s', '--ssn_list', help='SSN File', required=True)
        self.parser.add_argument(
            '-i', '--input', help='Input File', required=True)
        self.parser.add_argument(
            '-o', '--output', help='Output File', required=True)

    def get_args(self,):
        return self.parser.parse_args()

def main():
	args = Parser().get_args()
	input_file = args.input
	output_file = args.output
	path_ssn = args.ssn_list

	"""
		Shuffle SSN
	"""
	with os.scandir(path_ssn) as dp:
		for i in dp:
			print("="*100)
			file_name = os.path.join(path_ssn, i.name)
			state = i.name.split(".")[0]

			print(f"Start shuffle SSN list: {state}")
			shuffle_file_name = f'{path_ssn}/shuf_ssn.txt'
			command = f'shuf {file_name} -o {shuffle_file_name}'
			sub = subprocess.run(command, check=True,  shell=True)
			shutil.move(shuffle_file_name, file_name)
			print("Shuffle Done")
			print("="*100)

	"""
		Get Line Size
	"""
	# line_size = 10
	# with open(file_name, 'r') as in_file:
	# 	line_size = len(str(in_file.readline()))


	"""
		Insert SSN
	"""
	state_pos = {}
	state_line_size = {}
	with open(output_file, mode='w') as out_file:
		with open(input_file, 'r') as in_file:
			for line_number, line in enumerate(in_file, 1):
				try:
					item = json.loads(line)
					state = item['state']
					file_name = os.path.join(path_ssn, f'{state}.txt')
					if state not in state_pos:
						state_pos[state] = 0
						line_size = 10
						with open(file_name, 'r') as ssn_file:
							line_size = len(str(ssn_file.readline()))
							state_line_size['state'] = line_size

					ssn = get_ssn(file_name, state_pos[state], state_line_size['state'])
					state_pos[state] = state_pos[state] + 1
					if ssn:
						item["ssn"] = ssn
						print(f"Inserted SSN for line: {line_number}")
					else:
						print(f"No SSN for line: {line_number}")

					out_file.write(json.dumps(item))
					out_file.write("\n")
				except:
					continue


	for state in state_pos:
		file_name = os.path.join(path_ssn, f'{state}.txt')
		print("="*100)
		print(f'Remove used SSNs for {state}')
		remove_ssn(file_name, state_pos[state])

if __name__ == '__main__':
	main()
