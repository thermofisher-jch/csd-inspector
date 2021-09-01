# !/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import os.path
import re

import pandas as pd

from IonInspector.reports.diagnostics.common.inspector_utils import (
    print_info,
    write_results_from_template,
)
from reports.diagnostics.Purification_Reagent_Lot_Summary.pure_utility import \
    find_purification_files
from reports.diagnostics.common.quantum_data_source import inject_quant_data_source


def execute(archive_path, output_path, _archive_type):
    find_purification_files(archive_path, required=set(["Quant_summary"]))
    raise ValueError("Reagent Lot Report Not Available Yet")


DEBUG_FILE_BARCODE_PATTERN = re.compile("^ (.*) for 91(\d{5,9})10(\d{4,15})17(\d{6})$")

DEBUG_FILE_BARCODE_LINE_FILTER = lambda line: line.find(b"doesPatternMatch") > 0

DEBUG_FILE_LINE_DATE_PATTERN = re.compile(r'^(?P<Date>\w{3}\s+\d{1,2},\s+\d{2}:\d{2}:\d{2})')


def find_run_start():
    """
    This routine is shared by multiple Purification diagnostics, but is not universal to all
    instrument types.  Until we implement packaging for instrument types, there is no clean way
    to share this code without over-sharing it, so for now forgive the repetition as well as
    the repetitive re-computation...
    """

def parse_row(row):
    tokens = DEBUG_FILE_BARCODE_PATTERN.split(row)
    date_src = tokens[3]
    date_src = "%s-%s-%s" % (date_src[0:2], date_src[2:4], date_src[4:6])
    return [tokens[0], row, tokens[1], date_src, tokens[2]]


def execute_take_one(archive_path, output_path, _archive_type):
    files_config = find_purification_files(archive_path)
    quant_source = inject_quant_data_source(files_config)
    start_time = quant_source.run_execution_time
    with open(os.path.join(archive_path, "debug"), "rb") as fp:
        # First, scan forward to the right date range.
        for line in fp:
            matched = DEBUG_FILE_LINE_DATE_PATTERN.findall(line)
            if len(matched) != 1:
                continue;
            line_date = pd.to_datetime(matched[0],
                format="%b %d, %H:%M:%S", errors='coerce')
            if line_date.month == 11 and start_time.month == 0:
                line_date = line_date.replace(year=start_time.year - 1)
            else:
                line_date = line_date.replace(year=start_time.year)
            if line_date >= start_time:
                print("Found " + start_time + " at :: " + line)
                break
        # Next look for the barcode lines
        details = []
        for line in fp:
            if DEBUG_FILE_BARCODE_LINE_FILTER(line):
                details.append(
                    parse_row(line.rsplit(b":", 1)[1])
                )
        run_details = {"Consumable Information": details}

    write_results_from_template(
        {"other_runDetails": run_details},
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )
    return print_info("See results for details.")

if __name__ == "__main__":
    archive_path_arg, output_path_arg, archive_type_arg = sys.argv[1:4]
    execute(archive_path_arg, output_path_arg, archive_type_arg)