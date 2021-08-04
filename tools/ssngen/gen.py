import os
import re
from itertools import product
from collections import defaultdict

PATH_SSN_PREFIX = "ssn_prefix.txt"

state_range_pattern = re.compile(r"([A-Z]{2})\s*-\s*(\d.*)")
range_split_pattern = re.compile(r"[\,\|]")


def main():
    range_by_state = defaultdict(list)

    with open(PATH_SSN_PREFIX, "r") as file:
        for row in file:
            match = state_range_pattern.findall(row)
            if not match:
                continue
            state, range_values = match[0]
            range_values = range_split_pattern.split(range_values)
            for range_value in range_values:
                if "-" in range_value:
                    range_by_state[state].extend([
                        *range(
                            int(range_value.split("-")[0]),
                            int(range_value.split("-")[1]) + 1,
                        )
                    ])
                else:
                    range_by_state[state].append(range_value)

    total = len(list(range_by_state.keys()))
    for index, (state_name, state_range) in enumerate(range_by_state.items(), 1):
        if not os.path.exists("ssn"):
            os.makedirs("ssn")

        file_name = f"./ssn/{state_name}.txt"
        with open(file_name, "w") as f:
            suffix_groups = list(
                product(range(1, 99 + 1), range(1, 9999 + 1))
            )  # {GG}-{SSSS}
            for (second, third) in suffix_groups:
                second = "{0:0>2}".format(second)
                third = "{0:0>4}".format(third)

                if (
                    not re.search(
                        r"(?=(\d+)\1+(.*))(\d+?)\3+\2$", f"{second}{third}"
                    )
                    and second not in third
                ):  # Check if duplicate blocks
                    suffix = f"{second}-{third}"
                    for first in state_range:
                        ssn = f"{str(first).zfill(3)}-{suffix}\n"
                        f.write(ssn)
        print(f"Done {index} of {total} State: {state_name}")


if __name__ == "__main__":
    main()

