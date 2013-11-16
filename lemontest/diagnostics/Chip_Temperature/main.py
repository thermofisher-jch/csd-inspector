#!/usr/bin/env python
# -*- coding: UTF-8 -*-

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
    if "ChipTemperature" not in explog:
        return "ChipTemperature missing from explog_final.txt", False

    if explog.get('PGM HW', None) == '1.1':
        return "Not needed for PGM 1.1", False

    return explog, True


def report(data):
    temperature = float(data["ChipTemperature"].split(" - ")[1])
    if temperature < 48.0:
        print("Alert")
        print(40)
        print(u"Chip temperature {:.2f} C is too cold.".format(temperature))
    elif temperature > 51:
        print("Alert")
        print(40)
        print(u"Chip temperature {:.2f} C is not cool.".format(temperature))
    else:
        print("OK")
        print(10)
        print(u"Chip temperature {:.2f} C is just right.".format(temperature))
        

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
