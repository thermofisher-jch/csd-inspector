#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *

try:
    thresholds = {
        "314": 6.0,
        "316": 8.0,
        "318": 10.0,
        "P1": 170,
        "520": 140,
        "530": 140,
        "540": 170,
    }

    archive_path, output_path = sys.argv[1:3]
    data = read_explog(archive_path)
    chip_type = get_chip_type_from_exp_log(data)

    # check to see if the we have a lookup value for the chip type
    if chip_type not in thresholds:
        raise Exception("No known thresholds for chip type " + chip_type)

    # find the correct key for the noise value
    noise = data.get('ChipNoise', None) or data.get('Noise', None)
    if not noise:
        raise Exception("The noise value could not be found in the log.")
    noise = float(noise)

    if noise > thresholds[chip_type]:
        print_alert("Chip noise " + str(noise) + " is too high for chip type " + chip_type + ".")
    else:
        print_ok("Chip noise " + str(noise) + " is low enough for chip type " + chip_type + ".")

except Exception as exc:
    print_na(str(exc))


