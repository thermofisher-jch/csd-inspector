#!/usr/bin/env python

import csv
import datetime
import json
import os
import sys

from IonInspector.reports.diagnostics.common.inspector_utils import (
    print_alert,
    print_info,
)


def get_valk_lib_prep_data(lines, fields=[]):
    # Read csv
    run_log_data = {"labels": [], "rows": []}

    csv_file = csv.DictReader(lines, delimiter=",")
    # Get rows
    for row in csv_file:
        if row["time"] == "time":
            break
        # Add data
        new_row = []
        for field, display_name, formatter in fields:
            if row.get(field) is None:
                new_row.append(None)
            else:
                new_row.append(formatter(row.get(field)))
        run_log_data["rows"].append(new_row)

    # Make labels
    run_log_data["labels"] = [display_name for field, display_name, formatter in fields]

    return run_log_data


def convert_time_lib_prep(value):
    return float(datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S").strftime("%s"))


TARGET_TEMP_FIELDS = [
    # Time
    ["time", "Time (s)", convert_time_lib_prep],
    # Temps
    ["PCRTemp1", "PCRTemp1 (c)", lambda x: float(x)],
    ["PCRTemp2", "PCRTemp2 (c)", lambda x: float(x)],
    ["PCRTemp3", "PCRTemp3 (c)", lambda x: float(x)],
    ["ChipHeatTemp", "ChipHeatTemp (c)", lambda x: float(x)],
    ["MagSepTemp", "MagSepTemp (c)", lambda x: float(x)],
    ["ReagentBayTemp1", "Zone 1+3 Temp (c)", lambda x: float(x)],
    ["ReagentBayTemp2", "Zone 2+4 Temp (c)", lambda x: float(x)],
]

TARGET_FAN_FIELDS = [
    # Time
    ["time", "Time (s)", convert_time_lib_prep],
    # Fans
    ["ChipFanSpeed", "ChipFanSpeed", float],
]


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    template_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "results.html"
    )
    results_path = os.path.join(output_path, "results.html")
    run_log_csv_path = os.path.join(archive_path, "CSA", "libPrep_log.csv")

    if not os.path.exists(run_log_csv_path):
        return print_alert("Could not find libPrep_log.csv!")

    with open(run_log_csv_path) as fp:
        run_log_temp_data = get_valk_lib_prep_data(fp.readlines(), TARGET_TEMP_FIELDS)

    with open(run_log_csv_path) as fp:
        run_log_fan_data = get_valk_lib_prep_data(fp.readlines(), TARGET_FAN_FIELDS)

    with open(template_path, "r") as template_file:
        with open(results_path, "w") as results_file:
            results_file.write(
                template_file.read()
                .replace('"%raw_temp_data%"', json.dumps(run_log_temp_data))
                .replace('"%raw_fan_data%"', json.dumps(run_log_fan_data))
            )

    # Write out status
    return print_info("See results for flow, fan, and temperature plots.")


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
