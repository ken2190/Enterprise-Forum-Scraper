import argparse, logging

main_parser_arguments = [
    {
        "args": ("-scrape", "--scrape"),
        "kwargs": {"help": "Do Scraping", "action": "store_true"},
    },
    {
        "args": ("-parse", "--parse"),
        "kwargs": {"help": "Do parsing", "action": "store_true"}
    },
    {
        "args": ("-t", '--template'),
        "kwargs": {"help": argparse.SUPPRESS, "required": False}
    },
    {
        "args": ("-i", '--input_path'),
        "kwargs": {"help": argparse.SUPPRESS, "required": False}
    },
    {
        "args": ("-o", '--output'),
        "kwargs": {"help": argparse.SUPPRESS, "required": False}
    },
    {
        "args": ("-x", '--proxy'),
        "kwargs": {"help": argparse.SUPPRESS, "required": False}
    },
    {
        "args": ("-ser", '--server'),
        "kwargs": {"help": argparse.SUPPRESS, "required": False}
    },
    {
        "args": ("-site", '--sitename'),
        "kwargs": {"help": argparse.SUPPRESS, "required": False}
    },
    {
        "args": ("-usr", '--user'),
        "kwargs": {"help": argparse.SUPPRESS, "required": False}
    },
    {
        "args": ("-pwd", '--password'),
        "kwargs": {"help": argparse.SUPPRESS, "required": False}
    },
    {
        "args": ("-w", '--wait_time'),
        "kwargs": {"help": argparse.SUPPRESS, "required": False}
    },
    {
        "args": ("-ts", '--topic_start'),
        "kwargs": {"help": argparse.SUPPRESS, "required": False}
    },
    {
        "args": ("-te", '--topic_end'),
        "kwargs": {"help": argparse.SUPPRESS, "required": False}
    },
    {
        "args": ("-rs", '--rescan'),
        "kwargs": {"help": argparse.SUPPRESS, "action": 'store_true'}
    },
    {
        "args": ("-up", '--update'),
        "kwargs": {"help": argparse.SUPPRESS, "action": 'store_true'}
    },
    {
        "args": ("-uo", '--useronly'),
        "kwargs": {"help": argparse.SUPPRESS, "action": 'store_true'}
    },
    {
        "args": ("-fr", '--firstrun'),
        "kwargs": {"help": argparse.SUPPRESS, "action": 'store_true'}
    },
    {
        "args": ("-s", '--start_date'),
        "kwargs": {"help": argparse.SUPPRESS, "required": False}
    },
    {
        "args": ("-e", '--end_date'),
        "kwargs": {"help": argparse.SUPPRESS, "required": False}
    },
    {
        "args": ("-b", '--banlist'),
        "kwargs": {"help": argparse.SUPPRESS, "action": 'store_true'}
    },
    {
        "args": ("-l", '--list'),
        "kwargs": {"help": argparse.SUPPRESS, "action": 'store_true'}
    },
    {
        "args": ("-ch", '--channel'),
        "kwargs": {"help": argparse.SUPPRESS, "required": False}
    },
    {
        "args": ("-k", '--kill'),
        "kwargs": {"help": argparse.SUPPRESS, "required": False}
    },
    {
        "args": ("-gather",),
        "kwargs": {"help": argparse.SUPPRESS, "action": 'store_true'}
    },
    {
        "args": ("-scan", '--scan'),
        "kwargs": {"help": 'Do scan db ip port', "action": 'store_true'}
    },
    {
        "args": ('--get_users',),
        "kwargs": {
            "help": 'Scrape forum users',
            "action": 'store_true',
            "default": False
        }
    },
    {
        "args": ('--no_proxy',),
        "kwargs": {
            "help": 'Disable proxies',
            "action": 'store_true',
            "default": None
        }
    },
    {
        "args": ('--proxy_countries',),
        "kwargs": {
            "help": 'Comma-delimited list of proxy countries',
            "default": None,
            "type": lambda val: [c.strip().lower() for c in val.split(',')]
        }
    },
    {
        "args": ('--use_vip',),
        "kwargs": {
            "help": 'Use VIP proxies',
            "action": 'store_true',
            "default": None
        }
    },
    {
        "args": ("-post", '--post'),
        "kwargs": {"help": 'Post processing', "action": 'store_true'}
    },
    {
        "args": ("-c", '--checkonly'),
        "kwargs": {"help": 'Limit missing author and date file', "action": 'store_true'}
    }
]

default_logging_config = {
    "level": logging.INFO,
    "format":'[%(asctime)s] %(message)s',
    "datefmt":"%Y-%m-%d %H:%M:%S"
}
