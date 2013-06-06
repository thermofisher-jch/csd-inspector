#!/usr/bin/env python

import sys
import os


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
    path = os.path.join(archive_path, "explog_final.txt")
    if not os.path.exists(path):
        return "explog_final.txt missing", False

    explog = load_explog(path)
    if "PGMPressure" not in explog:
        return "PGMPressure missing from explog_final.txt", False

    if explog['PGM HW'] == '1.1':
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