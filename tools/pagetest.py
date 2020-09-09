import re
from glob import glob
OUPUT_FOLDER = 'paginationtest'

pagination_pattern = re.compile(r'\d+-(\d+)$')
thread_name_pattern = re.compile(r'(\d+)-.*')

files = [x.split('/')[-1] for x in glob(f'{OUPUT_FOLDER}/*')]

def locate(files):
	result = []
	thread_names = set([thread_name_pattern.search(x)[1] for x in files])
	for thread_name in thread_names:
		paginations = set([thread_name_pattern.search(x)[1]==thread_name and int(pagination_pattern.search(x)[1]) for x in files])
		if not 1 in paginations:
			result.append(thread_name)
	return result

print(locate(files))