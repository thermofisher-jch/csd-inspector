#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *

REPORT_LEVEL_INFO = 0
REPORT_LEVEL_WARN = 1
REPORT_LEVEL_ALERT = 2


# the ranges based on chip type for which the gain value is valid
PGM_GAIN_RANGE = (0.67, 0.71)
PROTON_S5_GAIN_RANGE = (0.9, 1.2)
gain_ranges = {
    "314": PGM_GAIN_RANGE,
    "316": PGM_GAIN_RANGE,
    "318": PGM_GAIN_RANGE,
    "P1": PROTON_S5_GAIN_RANGE,
    "520": PROTON_S5_GAIN_RANGE,
    "530": PROTON_S5_GAIN_RANGE,
    "540": PROTON_S5_GAIN_RANGE
}

noise_thresholds = {
    "314": 6.0,
    "316": 8.0,
    "318": 10.0,
    "P1": 170,
    "520": 140,
    "530": 140,
    "540": 170,
}

electrode_ranges = {
    "314": (0.4, 1.20),
    "316": (0.4, 1.20),
    "318": (0.4, 1.20),
    "P1": (170.0, 170.0),
}

try:
    # get the path to the log file
    archive_path, output_path, archive_type = sys.argv[1:4]
    data = read_explog(archive_path)
    check_supported(data)
    chip_type = get_chip_type_from_exp_log(data)
    report_level = REPORT_LEVEL_INFO

    # check to see if the we have a lookup value for the chip type
    if chip_type not in noise_thresholds:
        raise Exception("No known thresholds for chip type " + chip_type)

    if chip_type not in gain_ranges:
        raise Exception("No known range for chip type " + chip_type)

    if "Gain" not in data and "ChipGain" not in data:
        raise Exception("No chip gain recorded.")

    # find the correct key for the noise value
    noise = data.get('ChipNoise', None) or data.get('Noise', None)
    if not noise:
        raise Exception("The noise value could not be found in the log.")
    noise = round(float(noise), 2)

    noise_alert = noise > noise_thresholds[chip_type]
    noise_report = "Chip noise " + str(noise) + (" is too high." if noise_alert else " is low enough.")
    if noise_alert:
        noise_report = "<b>" + noise_report + "</b>"
        report_level = max(report_level, REPORT_LEVEL_ALERT)

    # detect issues with the gain
    low, high = gain_ranges[chip_type]
    gain = round(float(data["Gain"] if "Gain" in data else data["ChipGain"]), 2)
    if gain > high:
        gain_report = "Chip gain {} is high.".format(gain)
    elif gain < low:
        gain_report = "Chip gain {} is low.".format(gain)
    else:
        gain_report = "Chip gain {} is within range.".format(gain)

    reports = [noise_report, gain_report]

    # detect reference electrode record indicating pgm and look for issues
    electode_alert = False
    if "Ref Electrode" in data and chip_type in electrode_ranges:
        low, high = electrode_ranges[chip_type]
        gain = round(float(data["Ref Electrode"].split(' ')[0]), 2)
        if gain > high:
            electrode_report = "Reference Electrode {} is high.".format(gain)
            electode_alert = True
        elif gain < low:
            electrode_report = "Reference Electrode {} is low.".format(gain)
            electode_alert = True
        else:
            electrode_report = "Reference Electrode {} is within range.".format(gain)

        if electode_alert:
            electrode_report = "<b>" + electrode_report + "</b>"
        reports.append(electrode_report)

    # report here
    if report_level == REPORT_LEVEL_ALERT:
        print_alert(" | ".join(reports))
    elif report_level == REPORT_LEVEL_WARN:
        print_warning(" | ".join(reports))
    else:
        print_info(" | ".join(reports))

except Exception as exc:
    print_na(str(exc))


