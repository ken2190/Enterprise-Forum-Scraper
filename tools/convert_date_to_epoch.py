import json
import traceback
import argparse
import dateparser


class Parser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="Parsing Filter JSON Parameters"
        )
        self.parser.add_argument("-i", "--input", help="Input File", required=True)
        self.parser.add_argument("-o", "--output", help="Output File", required=True)
        self.parser.add_argument(
            "-k",
            "--keep",
            help="list of fields to keep (comma separated). "
                 "Everything else will be removed.",
            required=False,
        )
        self.parser.add_argument(
            "-d",
            "--replace_date",
            help="convert date field to epoch",
            action="store_true",
            default=True,
        )
        self.parser.add_argument(
            "-f",
            "--format",
            help="Insert formatting for elasticsearch",
            action="store_true",
            default=True,
        )

    def get_args(self):
        return self.parser.parse_args()


def filter_json(data, parent_key, filter_fields):
    """
    Keep only specified property for nested json
    """
    if isinstance(data, list) or isinstance(data, dict):
        for key in list(data.keys()):
            path = str(parent_key + "/" + key)
            if path.strip("/") not in filter_fields and not len(
                [s for s in filter_fields if s.startswith(path.strip("/") + "/")]
            ):
                del data[key]
            else:
                if not data[key]:
                    del data[key]
                else:
                    if isinstance(data[key], dict):
                        filter_json(data[key], parent_key + "/" + key, filter_fields)
                    elif isinstance(data[key], list):
                        for val in data[key]:
                            if isinstance(val, str):
                                pass
                            elif isinstance(val, list):
                                pass
                            else:
                                filter_json(val, parent_key + "/" + key, filter_fields)


def process_date(date_str):
    try:
        date = dateparser.parse(str(date_str))
        parsed_date = str(date.timestamp())
    except Exception as err:
        parsed_date = date_str
    return parsed_date


def process_line(out_file, single_json, args):
    json_response = json.loads(single_json)
    if args.keep:
        out_fields = args.keep
        out_fields = [i.strip() for i in out_fields.split(",")] if out_fields else []
        filter_json(json_response, "", out_fields)

    final_data = dict()

    if "_source" in json_response:
        data = json_response["_source"].items()
    else:
        data = json_response.items()
    for key, value in data:
        if key in ["date"] and args.replace_date:
            date = process_date(value)
            final_data.update({"date": date})
            continue
        final_data.update({key: value})
    if args.format:
        filtered_json = {"_source": final_data}
    else:
        filtered_json = final_data
    out_file.write(json.dumps(filtered_json, ensure_ascii=False) + "\n")


def main():
    try:
        args = Parser().get_args()
    except SystemExit:
        help_message = """
            Usage: jproc.py [-h] -i INPUT -o OUTPUT [-k KEEP] [-d] [-am] [-nm] [-f]\n
            Arguments:
            -i  | --input  INPUT:         Input File
            -o  | --output OUTPUT:          Output File

            Optional:
            -k           | --keep KEEP_LIST:         List of fields to keep (comma separated).
            -d           | --replace_date:           Replace date to epoch (default True)
            -f           | --format                  Insert formatting for elasticsearch (default True)
            """
        print(help_message)
        raise

    input_file = args.input
    output_file = args.output
    with open(output_file, "w") as out_file:
        with open(input_file, "r") as fp:
            for line_number, single_json in enumerate(fp, 1):
                try:
                    process_line(out_file, single_json, args)
                    print("Writing line number:", line_number)
                except Exception:
                    print("Error in line number:", line_number)
                    traceback.print_exc()
                    break


if __name__ == "__main__":
    main()
