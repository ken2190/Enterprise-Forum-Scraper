dataset_1 = {
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


dataset_2 = {
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