#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import os
from inspector_utils import *


def validate(archive_path):
    explog = read_explog(archive_path)
    if "PGMTemperature" not in explog:
        return "PGMTemperature missing from explog_final.txt", False

    if explog.get('PGM HW', None) == '1.1':
        return "Not needed for PGM 1.1", False

    return explog, True


def report(data):
    temperature = float(data["PGMTemperature"].split(" - ")[1])
    if temperature < 26:
        print("Alert")
        print(40)
        print(u"PGM temperature {:.2f} C is too cold.".format(temperature))
    elif temperature > 34:
        print("Alert")
        print(40)
        print(u"PGM temperature {:.2f} C is not cool.".format(temperature))
    else:
        print("OK")
        print(10)
        print(u"PGM temperature {:.2f} C is just right.".format(temperature))
        

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
