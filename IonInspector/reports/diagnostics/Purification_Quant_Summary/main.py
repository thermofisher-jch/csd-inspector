# -*- coding: utf-8 -*-
# !/usr/bin/env python
import itertools
import os
import csv
import fnmatch
import copy
import re
from IonInspector.reports.diagnostics.common.inspector_utils import (
    print_info,
    write_results_from_template,
)

barcode_parser = re.compile("^ (.*) for 91(\d{5,9})10(\d{4,15})17(\d{6})$")

def execute(archive_path, output_path, _archive_type):
    with open(os.path.join(archive_path, "debug"), "rb") as fp:
        parts = set(line.rsplit(b":", 1)[1] for line in filter(select_matching_lines, fp))
    details = [parse_row(row) for row in set(
        line.rsplit(b":", 1)[1] for line in filter(select_matching_lines, fp)
    )]
    run_details = { "Consumable Information": details }

    write_results_from_template(
        {"other_runDetails": run_details },
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )

    return print_info("See results for details.")


def select_matching_lines(line):
    return line.index(b"doesPatternMatch") > 0

def parse_row(row):
    tokens = barcode_parser.split(row)
    date_src = tokens[3]
    date_src = "%s-%s-%s" % (date_src[0:2], date_src[2:4], date_src[4:6])
    return [tokens[0], row, tokens[1], date_src, tokens[2]]