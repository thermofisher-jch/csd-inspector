#!/usr/bin/env python

import os
import sys
from lemontest.diagnostics.common.inspector_utils import *


def get_lot_from_lines(log_lines, lot_type):
    """
    Helper method to grab the lot number from the lines variable
    :param log_lines: The lines in the log file
    :param lot_type: The specific type of lot looking for
    :return: The string value of the lot type
    """
    for lineIndex in range(len(log_lines)):
        line = log_lines[lineIndex].strip()

        if line.startswith('productDesc') and lot_type in line:
            lot_line = log_lines[lineIndex + 2]
            key_value = lot_line.split(":")
            if key_value[0] != "lotNumber":
                raise Exception("Did not find a lot number in expected location")
            return "<b>" + key_value[1].strip() + "</b>"
    return '<b>Unknown</b>'

archive, output, archive_type = sys.argv[1:4]
try:
    data = read_explog(archive)
    check_supported(data)

    # get the archive and output from argument list
    path = os.path.join(archive, "InitLog.txt")

    # read all the lines into an array
    with open(path) as f:
        lines = f.readlines()

    # construct the html response message
    cleaningLot = "Cleaning " + get_lot_from_lines(lines, 'Ion S5 Cleaning Solution')
    sequencingLot = "Sequencing " + get_lot_from_lines(lines, 'Ion S5 Sequencing Reagent')
    washLot = "Wash " + get_lot_from_lines(lines, 'Ion S5 Wash Solution')

    print_info(" | ".join([cleaningLot, sequencingLot, washLot]))
except Exception as exc:
    print_na(str(exc))
