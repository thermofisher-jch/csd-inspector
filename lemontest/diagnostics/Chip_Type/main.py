#!/usr/bin/env python

import sys
import os
from inspector_utils import *


try:

    # get the path to the log file
    archive_path, output_path = sys.argv[1:3]
    data = read_explog(archive_path)

    # get the chip type
    if 'TsChipType' not in data:
        raise Exception("Chip type missing from explog_final.txt")

    print_info("Planned - " + data['TsChipType'])

except Exception as exc:
    print_na(str(exc))


