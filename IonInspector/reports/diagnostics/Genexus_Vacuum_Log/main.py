#!/usr/bin/env python

import csv
import datetime
import os
import sys


from reports.diagnostics.common.inspector_utils import (
    write_results_from_template,
    print_info,
)


def get_valk_vacuum_log_data(lines, fields=[], lane_col=3):
    # Read csv
    rows = []

    csv_file = csv.reader(lines, delimiter=",", quotechar='"')
    # Get rows
    for row in csv_file:
        # Add data
        new_row = {}
        for field, key, formatter in fields:
            if row[field] is None:
                new_row[key] = None
            else:
                new_row[key] = formatter(row[field])
        rows.append(new_row)

    return rows


def convert_time_vacuum(value):
    return datetime.datetime.strptime(value, "%Y_%m_%d-%H:%M:%S").strftime("%H:%M:%S")


TARGET_VACUUM_FIELDS = [
    [1, "time", convert_time_vacuum],
    [3, "lane", int],
    [23, "pump_duty_cycle", lambda x: round(float(x), 3)],
    [17, "time_to_target", lambda x: round(float(x), 3)],
    [19, "mean_pressure", lambda x: round(float(x), 3)],
    [25, "comment", lambda x: x],
    [25, "stage", lambda x: x.split(":")[0].lower()],
]


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    vacuum_log_csv_path = os.path.join(archive_path, "CSA", "vacuum_log.csv")

    with open(vacuum_log_csv_path) as fp:
        vacuum_log_data = get_valk_vacuum_log_data(
            fp.readlines()[:100], TARGET_VACUUM_FIELDS
        )

    write_results_from_template(
        {"log": vacuum_log_data},
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )

    # Write out status
    return print_info("See results for events.")


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
