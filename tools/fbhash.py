
import hmac, base64, json
from collections import OrderedDict

from settings import DATASET_HASH_KEY


test_data_1 = {
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

test_data_2 = {
	"numbers": {
		"positive_integer": 123,
		"negative_integer": -45,
		"float": 6.78,
		"e_notation": [
			9.1e+20,
			5e+32,
			6.78e-5,
			7.89E+45
		],
		"zero": 0,
		"positive_integers": [
			1,
			12,
			123
		],
		"negative_integers": [
			-4,
			-45,
			-456
		],
		"floats": [
			-1.23,
			0.0,
			1.23
		]
	},
	"strings": {
		"empty_string": "",
		"basic_string": "foobar",
		"newline": "a\nb",
		"non_ascii": "\ud83d\ude00",
		"escaped_double_quotes": "\" has ascii value 34",
		"string_encoded_number": "3.1415",
		"basic_strings": [
			"foo",
			"bar",
			"foobar",
			"foo bar"
		]
	},
	"other": {
		"boolean_true": True,
		"boolean_false": False,
		"null": None
	},
	"data": {
		"bigint": 123456789012345,
		"bigint-string": "123456789012345",
		"name": "Jane M. Doe",
		"url": "https://www.facebook.com/foo.bar/",
		"email": "abc@example.com",
	},
	"edge_cases": {
		"60-bit int": 1152921504606846976
	},
	"long string": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Elementum curabitur vitae nunc sed velit dignissim sodales ut eu. Purus in mollis nunc sed. Non curabitur gravida arcu ac tortor dignissim. Turpis nunc eget lorem dolor sed viverra. At tellus at urna condimentum mattis pellentesque id nibh tortor. Sapien faucibus et molestie ac feugiat sed lectus vestibulum. Elementum nibh tellus molestie nunc non blandit massa. Ultricies integer quis auctor elit sed vulputate. Et ultrices neque ornare aenean euismod. Massa placerat duis ultricies lacus sed turpis tincidunt id."
}


def keyed_hashing_algorithm(value):
	if value is None:
		return value

	value_string = str(value).lower().strip()
	value_bytes = value_string.encode('utf-8', errors='surrogatepass')
	hash_bytes = hmac.digest(DATASET_HASH_KEY.encode('utf-8'), value_bytes, 'sha256')
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


doit = hash_dataset(test_data_2, test_data_2)
print(json.dumps(doit, indent=4))

'''
current output of running this file. python fbhash.py
'''

'''
{
    "numbers": {
        "positive_integer": "lH7PGrhCgWu5EZiDGxhqDp1B6vZOiZpiW4wljGyUFIk=",
        "negative_integer": "rHdpVGt3cD44bKRyxRedWEEjag+Rf8F4AlE3dKGdprU=",
        "float": "kLXhk3WSlyfSPhbh04gAUSAQSs1NAnGzunOmgQ37yU8=",
        "e_notation": [
            "d/ByQCL34oujV5mjRpyc4BPpVPLNrKZV+Jq0aPgFSW8=",
            "YoUARpWDIEISHHXbVoMa/eUcLDbvPDY5AyxDObFTRMk=",
            "lEeIDPMzELEY2chgIG+CyBhjQeWGFyCibT0qa706LYA=",
            "8Cu5th9rOapd4z1fxFBysTNpId7utfjSkzVaJBWF7XY="
        ],
        "zero": "dAmBkJj0gBvEoz69NzIbgMGKkcFwufbDxHKob7oZFL8=",
        "positive_integers": [
            "ChWxbELCMFLEfnGsBHWbOzVrQ0dy06TGelJVrbdVIhU=",
            "ubX6uXkUyGqPbzAfzHOSGVQ26Rrsu9ET0yFGl+gpXAU=",
            "lH7PGrhCgWu5EZiDGxhqDp1B6vZOiZpiW4wljGyUFIk="
        ],
        "negative_integers": [
            "K7Dck9sVZiFCVLWX/sxuMJ9Rk9JuYv+YDkGpWR3yths=",
            "rHdpVGt3cD44bKRyxRedWEEjag+Rf8F4AlE3dKGdprU=",
            "w4fkYzKGgOpokdAn4rO3XjoFUveUEaqCqoRUwJo0mwo="
        ],
        "floats": [
            "AzxBffj/uhIT7QRh3Cvk7m7a6sp6bOlf8y8Q3mJ7TuY=",
            "sT+pkWbuFWBtCRCA3TsxV04o/1x6t4TZAuxSvs88stM=",
            "j8lz4xERnt4rJ7uCfyicyWy2qEXXrReWB60Dau2ENJU="
        ]
    },
    "strings": {
        "empty_string": "JlXjnP8yYK0Hx6ffW6yDrkUK8yEjcdYVxT7oYLqka1M=",
        "basic_string": "x5rtE313pdjhsnJTkiJEubvoVhwgbSyvSA3AA3bJca8=",
        "newline": "1FC/dtS38ydMAGtWY6+qhbaqauIHGJF24+xobwtnmPQ=",
        "non_ascii": "u39221UO3IvHq4Sd9jyhu0cT+QRsI8Y14dCRdZE9EY8=",
        "escaped_double_quotes": "AiXKxCZtKfUhldfinvWrvKgDWSfN2CXeXwmOjq9XKa0=",
        "string_encoded_number": "A02zCKWXl2PIA1UXR8tDgB3NM7ydSQtrhTGWiUNIE0Y=",
        "basic_strings": [
            "t17EvmXyWfE1FY0qBli+QDwn29CmI+Q5ZSxfls3tTF0=",
            "Ks0uaD+SLrPusOQHYNHIc7sN9r+8gM8Z3NdIFZayZb4=",
            "x5rtE313pdjhsnJTkiJEubvoVhwgbSyvSA3AA3bJca8=",
            "dA6zoEAjApbgQShIGU8lOd67tapahaYiT8P+kXMoQaU="
        ]
    },
    "other": {
        "boolean_true": "lMTtoQNvqveZ+tCqMK8nht+Va//MCnF0+ayXL8wrnRk=",
        "boolean_false": "YJYbTg0WTs4gSxaHSiaU5tDS57/SPcAoLxpLwZqjc7w=",
        "null": null
    },
    "data": {
        "bigint": "h2F1c1Ys1ne6jpxdZNI8BKaB6uwgOdHm781iusNhKTc=",
        "bigint-string": "h2F1c1Ys1ne6jpxdZNI8BKaB6uwgOdHm781iusNhKTc=",
        "name": "7UG9jSsdXY1sMSHnFnbYzdV/sk5TY6hwd1hCizH3XO0=",
        "url": "p7MfT4XKZ+C4Z5BArgHWxY84keepaX2gQwyuR2RI5is=",
        "email": "aAYdz1+MFCnw2c5Rrsbrs3yy1OAEjtHos/kVBJpQIlY="
    },
    "edge_cases": {
        "60-bit int": "8V30LzNzQz2/RuBmgrYI+bMLQMHk2zY1w/UvnPgWZxU="
    },
    "long string": "YfYXM9KB0yShxLxx1l+q/ZIxpRlnIVxGyH5/eHnQpb4="
}

'''

