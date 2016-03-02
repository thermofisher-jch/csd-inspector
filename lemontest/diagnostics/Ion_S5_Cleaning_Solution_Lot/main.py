#!/usr/bin/env python

import os
import sys
from inspector_utils import *

PRODUCT_LINE = 'Ion S5 Cleaning Solution'

try:
    # get the archive and output from argument list
    archive, output = sys.argv[1:3]
    path = os.path.join(archive, "InitLog.txt")
    washLot = 'UNKNOWN'

    # read all the lines into an array
    with open(path) as f:
        lines = f.readlines()

    for lineIndex in range(len(lines)):
        line = lines[lineIndex].strip()

        if line.startswith('productDesc') and PRODUCT_LINE in line:
            washLotLine = lines[lineIndex + 2]
            keyValue = washLotLine.split(":")
            if keyValue[0] != "lotNumber":
                raise Exception("Did not find a lot number in expected location")
            washLot = keyValue[1].strip()
            break

    print_info(washLot)
except Exception as exc:
    print_na(str(exc))
