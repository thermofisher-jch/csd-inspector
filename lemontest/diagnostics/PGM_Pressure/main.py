#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *

try:
    archive_path, output_path = sys.argv[1:3]
    explog = read_explog(archive_path)
    if "PGMPressure" not in explog:
        raise "PGMPressure missing from explog_final.txt"

    pressure = float(explog["PGMPressure"].split(" - ")[1])
    if pressure < 9.5:
        print_alert("PGM pressure {:.2f} is too low.".format(pressure))
    elif pressure > 11:
        print_alert("PGM pressure {:.2f} is high.".format(pressure))
    else:
        print_ok("PGM pressure {:.2f} is just right.".format(pressure))
except Exception as exc:
    print_na(str(exc))
