#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *


# the ranges based on chip type for which the gain value is valid
ranges = {
        "314": (0.67, 0.70),
        "316": (0.67, 0.70),
        "318": (0.67, 0.70),
        "P1": (170.0, 170.0),
        "520": (1.0, 1.1),
        "530": (1.0, 1.1),
        "540": (1.0, 1.1)
    }

try:
    # get the path to the log file
    archive_path, output_path = sys.argv[1:3]
    data = read_explog(archive_path)

    chip_type = get_chip_type_from_exp_log(data)

    if chip_type not in ranges:
        raise Exception("No known range for chip type " + chip_type)

    if "Gain" not in data and "ChipGain" not in data:
        raise Exception("No chip gain recorded.")

    low, high = ranges[chip_type]
    gain = float(data["Gain"] if "Gain" in data else data["ChipGain"])
    if gain > high:
        print_alert("Chip gain {:.2f} is too high for chip type '{}'.".format(gain, chip_type))
    elif gain < low:
        print_alert("Chip gain {:.2f} is a to low for chip type '{}'.".format(gain, chip_type))
    else:
        print_ok("Chip gain {:.2f} is within range for chip type '{}'.".format(gain, chip_type))

except Exception as exc:
    print_na(str(exc))


