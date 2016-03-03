#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *


# the ranges based on chip type for which the gain value is valid
ranges = {
        "314": (0.4, 1.20),
        "316": (0.4, 1.20),
        "318": (0.4, 1.20),
        "P1": (170.0, 170.0),
    }

try:

    # get the path to the log file
    archive_path, output_path = sys.argv[1:3]
    data = read_explog(archive_path)

    # get the chip type
    if "ChipType" not in data:
        raise Exception("ChipType missing from explog_final.txt")

    chip_type = data["ChipType"][:3]
    chipTypeString = data["ChipType"]
    chip_type = data["ChipType"][:min(3, len(chipTypeString))]

    if chip_type not in ranges:
        raise Exception("No known range for chip type " + chip_type)

    if "Ref Electrode" not in data:
        raise Exception("No chip gain recorded.")

    low, high = ranges[chip_type]
    gain = float(data["Ref Electrode"].split(' ')[0])
    if gain > high:
        print("Alert")
        print(40)
        print("Chip gain {:.2f} is too high for chip type '{}'.".format(gain, chipTypeString))
    elif gain < low:
        print("Alert")
        print(30)
        print("Chip gain {:.2f} is a to low for chip type '{}'.".format(gain, chipTypeString))
    else:
        print("OK")
        print(10)
        print("Chip gain {:.2f} is within range for chip type '{}'.".format(gain, chipTypeString))

except Exception as exc:
    print("N/A")
    print(0)
    print(str(exc))


