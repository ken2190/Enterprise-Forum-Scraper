import logging

database_types = ["mongo", "es", "cassandra"]

noscrape_parser_arguments = [
	{
		"args": ("-t", "--type"),
		"kwargs": {"help": "Specify database type", "required": True, "choices": database_types}
	},
	{
		"args": ("-m", "--meta"),
		"kwargs": {"help": "Fetch metadata from public databases", 'action': 'store_true'},
	},
	{
		"args": ("-d", "--dump"),
		"kwargs": {"help": "Fetch data from public databases", "action": "store_true"}
	}
]

