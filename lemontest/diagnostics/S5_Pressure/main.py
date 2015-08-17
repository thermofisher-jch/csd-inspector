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
    if "PGMPressure" not in explog and "ProtonPressure" not in explog:
        return "Pressure missing from explog_final.txt", False

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