#!/usr/bin/env python

import sys
import os


def load_explog(path):
    data = {}
    for line in open(path):
        # Trying extra hard to accomodate formatting issues in explog
        datum = line.split(":", 1)
        if len(datum) == 2:
            key, value = datum
            data[key.strip()] = value.strip()
    return data


def validate(archive_path):
    path = os.path.join(archive_path, "explog_final.txt")
    if not os.path.exists(path):
        return "explog_final.txt missing", False

    explog = load_explog(path)

    if "ChipType" not in explog:
        return "ChipType missing from explog_final.txt", False
    chip_type = explog["ChipType"][:3]
    if chip_type != '900' and "Noise_90pct" not in explog:
        return "Noise_90pct missing from explog_final.txt", False
    elif chip_type == '900' and "ChipNoiseInfo" not in explog:
        return "ChipNoiseInfo missing from explog_final.txt", False

    return explog, True


def proton_correlated_noise(chip_noise_info):
    info = dict(x.split(":", 1) for x in chip_noise_info.split(" "))
    return float(info['Cor'])


def report(data):
    thresholds = {
        "314": 8.0,
        "316": 10.0,
        "318": 9.0,
        "900": (1.0, 2.0)
    }
    chip_type = data["ChipType"][:3]

    if chip_type == '900':
        noise = proton_correlated_noise(data["ChipNoiseInfo"])
        low, high = thresholds[chip_type]
        if noise > high:
            print("Alert")
            print(40)
            print("Chip noise {:.2f} is too high.".format(noise))
        elif noise > low:
            print("Warning")
            print(30)
            print("Chip noise {:.2f} is a little high.".format(noise))
        else:
            print("OK")
            print(20)
            print("Chip noise {:.2f} is low enough.".format(noise))
    else:
        noise = float(data["Noise_90pct"])
        if noise > thresholds[chip_type]:
            print("Alert")
            print(40)
            print("Chip noise {:.2f} is too high for a {}.".format(noise, chip_type))
        else:
            print("OK")
            print(10)
            print("Chip noise {:.2f} is low enough for a {}.".format(noise, chip_type))
        

def main():
    archive_path, output_path = sys.argv[1:3]
    data, valid = validate(archive_path)
    if not valid:
        print("N\A")
        print(0)
        print(data)
        sys.exit()
    else:
        report(data)

main()