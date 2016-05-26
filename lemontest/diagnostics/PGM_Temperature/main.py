#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
from lemontest.diagnostics.common.inspector_utils import *

try:
    archive_path, output_path = sys.argv[1:3]
    explog = read_explog(archive_path)
    if "PGMTemperature" not in explog:
        raise Exception("PGMTemperature missing from explog_final.txt")

    temperature = float(explog["PGMTemperature"].split(" - ")[1])
    if temperature < 26:
        print_alert(u"PGM temperature {:.2f} C is too cold.".format(temperature))
    elif temperature > 34:
        print_alert(u"PGM temperature {:.2f} C is not cool.".format(temperature))
    else:
        print_ok(u"PGM temperature {:.2f} C is just right.".format(temperature))
except Exception as exc:
    print_na(str(exc))

