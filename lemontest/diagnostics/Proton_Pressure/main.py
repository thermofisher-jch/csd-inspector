#!/usr/bin/env python

import sys
import os
from lemontest.diagnostics.common.inspector_utils import *


def validate(archive_path):
    explog = read_explog(archive_path)
    if "PGMPressure" not in explog and "ProtonPressure" not in explog:
        return "PGMPressure missing from explog_final.txt", False

    if explog.get('PGM HW', None) == '1.1':
        return "Not needed for PGM 1.1", False

    return explog, True


def report(data):
    if "PGMPressure" in data:
        pressure = data["PGMPressure"]
    else:
        pressure = data["ProtonPressure"]
    pressure = float(pressure.split(" ")[1])
    target_pressure = float(data["pres"])
    if target_pressure == 8.0:
        low, high = 7.8, 8.1
    else:
        low, high = 10.4, 10.6

    if pressure < low:
        print("Alert")
        print(40)
        print("Pressure {:.2f} is too low. (Target pressure {:.2f})".format(pressure, target_pressure))
    elif pressure > high:
        print("Alert")
        print(40)
        print("Pressure {:.2f} is high. (Target pressure {:.2f})".format(pressure, target_pressure))
    else:
        print("OK")
        print(10)
        print("Pressure {:.2f} is just right. (Target pressure {:.2f})".format(pressure, target_pressure))
        

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