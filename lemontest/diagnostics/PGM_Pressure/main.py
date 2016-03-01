#!/usr/bin/env python

import sys
import os
from inspector_utils import *

def load_explog(path):
    data = {}
    for line in open(path):
        # Trying extra hard to accomodate formatting issues in explog
        datum = line.split(": ", 1)
        if len(datum) == 2:
            key, value = datum
            data[key.strip()] = value.strip()
    return data


def validate(archive_path):
    explog = read_explog(archive_path)
    if "PGMPressure" not in explog:
        return "PGMPressure missing from explog_final.txt", False

    if explog.get('PGM HW', None) == '1.1':
        return "Not needed for PGM 1.1", False

    return explog, True


def report(data):
    pressure = float(data["PGMPressure"].split(" - ")[1])
    if pressure < 9.5:
        print("Alert")
        print(40)
        print("PGM pressure {:.2f} is too low.".format(pressure))
    elif pressure > 11:
        print("Alert")
        print(40)
        print("PGM pressure {:.2f} is high.".format(pressure))
    else:
        print("OK")
        print(10)
        print("PGM pressure {:.2f} is just right.".format(pressure))
        

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