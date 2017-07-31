#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
from lemontest.diagnostics.common.inspector_utils import *


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        explog = read_explog(archive_path)
        if "ChipTemperature" not in explog:
            raise Exception("ChipTemperature missing from explog_final.txt")

        temperature = float(explog["ChipTemperature"].split(" - ")[1])
        if temperature < 46:
            print_alert(u"Chip temperature {:.2f} C is too cold.".format(temperature))
        elif temperature > 54:
            print_alert(u"Chip temperature {:.2f} C is not cool.".format(temperature))
        else:
            print_ok(u"Chip temperature {:.2f} C is just right.".format(temperature))
    except Exception as exc:
        print_na(str(exc))

if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
