#!/usr/bin/env python
import os
import csv
import fnmatch
from IonInspector.reports.diagnostics.common.inspector_utils import (
    print_info,
    write_results_from_template,
)


def find_sample_name(rows):
    for row in rows:
        if len(row) < 2:
            continue
        if "sample name" in row[0].lower():
            return row[1]
    return "Unknown Sample"


def execute(archive_path, output_path, archive_type):
    info_per_sample = []

    for root, dirnames, filenames in os.walk(os.path.join(archive_path, "CSA")):
        for filename in fnmatch.filter(filenames, 'Info.csv'):
            with open(os.path.join(root, filename), "rb") as fp:
                info_rows = list(csv.reader(fp, delimiter=','))
                sample_name = find_sample_name(info_rows)
                info_per_sample.append([sample_name, info_rows])

    info_per_sample.sort(key=lambda x:x[0])

    write_results_from_template(
        {"info_per_sample": info_per_sample},
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )

    return print_info("See results for details.")
