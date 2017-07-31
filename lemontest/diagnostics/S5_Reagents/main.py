#!/usr/bin/env python

import os
import sys
from lemontest.diagnostics.common.inspector_utils import *


def get_lot_from_lines(log_lines, lot_types):
    """
    Helper method to grab the lot number from the lines variable
    :param log_lines: The lines in the log file
    :param lot_types: The specific type of lot looking for
    :return: The string value of the lot type
    """
    for lineIndex in range(len(log_lines)):
        line = log_lines[lineIndex].strip()

        if line.startswith('productDesc'):
            for lot_type in lot_types:
                if lot_type in line:
                    lot_line = log_lines[lineIndex + 2]
                    key_value = lot_line.split(":")
                    if key_value[0] != "lotNumber":
                        raise Exception("Did not find a lot number in expected location")
                    return "<b>" + key_value[1].strip() + "</b>"
    return '<b>Unknown</b>'


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        data = read_explog(archive_path)
        check_supported(data)

        # read all the lines into an array
        with open(os.path.join(archive_path, "InitLog.txt")) as f:
            lines = f.readlines()

        # read in carry forward
        base_caller = read_base_caller_json(archive_path)
        cf = float(base_caller["Phasing"]["CF"]) * 100

        # construct the html response message
        cleaningLot = "Cleaning Lot " + get_lot_from_lines(lines, ['Ion S5 Cleaning Solution'])
        sequencingLot = "Sequencing Lot " + get_lot_from_lines(lines, ['Ion S5 Sequencing Reagent', 'Ion S5 ExT Sequencing Reagent'])
        washLot = "Wash Lot " + get_lot_from_lines(lines, ['Ion S5 Wash Solution', 'Ion S5 ExT Wash Solution'])

        print_info(" | ".join([cleaningLot, sequencingLot, washLot]))

        # write out results.html
        with open(os.path.join(output_path, "results.html"), "w") as html_handle:
            # html header
            html_handle.write("<html><head></head><body>")

            # write out reagent image
            if os.path.exists(os.path.join(archive_path, 'InitRawTrace0.png')):
                html_handle.write("<h2 align='center'>Reagent Check</h2>")
                html_handle.write("<p style='text-align:center;'>")
                html_handle.write("<img src='../../InitRawTrace0.png' />")
                html_handle.write("</p>")

            # write out carry forward for checking reagent leaks
            html_handle.write("<h2 align='center'>Phasing - Carry Forward</h2>")
            html_handle.write("<p style='text-align:center;'>")
            html_handle.write("CF = {0:.2f}%".format(cf))
            html_handle.write("</p>")

            # html footer
            html_handle.write("</body></html>")

    except Exception as exc:
        handle_exception(exc, output_path)

if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)