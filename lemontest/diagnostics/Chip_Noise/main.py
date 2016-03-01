#!/usr/bin/env python

import sys
import os
from inspector_utils import *


def proton_correlated_noise(chip_noise_info):
    noise_info = dict(x.split(":", 1) for x in chip_noise_info.split(" "))
    return float(noise_info['Cor'])

# the thresholds for warning and alerts (-1 for invalid warning)
thresholds = {
        "314": (-1.0, 6.0),
        "316": (-1.0, 8.0),
        "318": (-1.0, 10.0),
        "P1": (-1.0, 170),
        "520": (-1.0, 140),
        "530": (-1.0, 140),
        "540": (-1.0, 170),
        "900": (1.0, 2.0)
    }

try:
    archive_path, output_path = sys.argv[1:3]
    data = read_explog(archive_path)

    if "ChipType" not in data:
        raise Exception("ChipType missing from explog_final.txt")

    chip_type = data["ChipType"][:3]
    if chip_type != '900' and "Noise_90pct" not in data:
        raise Exception("Noise_90pct missing from explog_final.txt")
    elif chip_type == '900':
        if "ChipNoiseInfo" not in data:
            raise Exception("ChipNoiseInfo missing from explog_final.txt")
        else:
            try:
                info = data.get("ChipNoiseInfo", "")
                noise = proton_correlated_noise(info)
            except (ValueError, KeyError) as err:
                raise Exception("Correlated chip noise is missing from explog_final.txt")

    chipTypeString = data["ChipType"]
    chip_type = data["ChipType"][:min(3, len(chipTypeString))]

    if chip_type not in thresholds:
        raise Exception("No known thresholds for chip type " + chip_type)

    low, high = thresholds[chip_type]
    if "ChipNoiseInfo" in data:
        noise = proton_correlated_noise(data["ChipNoiseInfo"])
        if noise > high:
            print("Alert")
            print(40)
            print("Chip noise {:.2f} is too high for chip type '{}'.".format(noise, chipTypeString))
        elif noise > low:
            print("Warning")
            print(30)
            print("Chip noise {:.2f} is a little high for chip type '{}'.".format(noise, chipTypeString))
        else:
            print("OK")
            print(10)
            print("Chip noise {:.2f} is low enough for chip type '{}'.".format(noise, chipTypeString))
    elif "Noise_90pct" in data:
        noise = float(data["Noise_90pct"])
        if noise > high:
            print("Alert")
            print(40)
            print("Chip noise {:.2f} is too high for a {}.".format(noise, chip_type))
        else:
            print("OK")
            print(10)
            print("Chip noise {:.2f} is low enough for a {}.".format(noise, chip_type))
except Exception as exc:
    print("N/A")
    print(0)
    print(str(exc))


