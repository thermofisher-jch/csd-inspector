#!/usr/bin/env python

import sys
import os
import ConfigParser

def load_explog(path):
    return dict(l.strip().split(": ", 1) for l in open(path) if ": " in l)


def validate(archive_path):
    path = os.path.join(archive_path, "explog_final.txt")
    if not os.path.exists(path):
        return "explog_final.txt missing", False

    explog = load_explog(path)
    if "ChipTemperature" not in explog:
        return "ChipTemperature missing from explog_final.txt", False
    return explog


def report(data):
    temperature = float(data["ChipTemperature"].split(" - ")[1])
    if 48.0 < temperature:
        print("Alert")
        print(40)
        print("Chip temperature {:.2f} is too cold.".format(temperature))
    elif temperature > 51:
        print("Alert")
        print(40)
        print("Chip temperature {:.2f} is not cool.".format(temperature))
    else:
        print("OK")
        print(10)
        print("Chip temperature {:.2f} is just right.".format(temperature))
        

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
