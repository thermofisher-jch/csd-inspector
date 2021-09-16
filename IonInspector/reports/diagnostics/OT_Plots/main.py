#!/usr/bin/env python

import csv
import json
import os
import sys
import time

from datetime import datetime

from IonInspector.reports.diagnostics.common.inspector_utils import (
    print_info,
    handle_exception,
)


def parse_timestamp(value):
    return time.mktime(
        datetime.strptime(value.replace("  ", " "), "%a %b %d %H:%M:%S %Y").timetuple()
    )


# Plots  csv header , display header, formatter
TARGET_TEMP_FIELDS = [
    # Time
    ["Timestamp", "Time (s)", parse_timestamp],
    # Temps
    ["Thermistor-0 Temperature", "Ambient Temperature (c)", lambda x: float(x)],
    ["Thermistor-1 Temperature", "Lid Temperature (c)", lambda x: float(x)],
    ["Thermistor-2 Temperature", "Block Temperature (c)", lambda x: float(x)],
    ["Thermistor-3 Temperature", "Internal Case Temperature (c)", lambda x: float(x)],
]

TARGET_FAN_FIELDS = [
    # Time
    ["Timestamp", "Time (s)", parse_timestamp],
    # Flow
    ["P_Sensor- Cur. Pressure", "Pressure Sensor (psi)", float],
    [
        "Motor Power- Oscillation",
        "Motor Power Oscillation (1000x)",
        lambda x: float(x) / 1000,
    ],
    ["Flowmeter0", "Flowmeter (lpm)", float],
]


def get_ot_log_data(path, fields):
    # Read csv
    ot_log_data = {"stages": [], "labels": [], "rows": []}

    with open(path, "rb") as ot_log_csv_file:
        # This csv has a bogus header line
        _ = ot_log_csv_file.readline()

        csv_file = csv.DictReader(ot_log_csv_file, delimiter=",", quotechar='"')
        # Get rows
        for row in csv_file:
            # Add data
            new_row = []
            for field, display_name, formatter in fields:
                if row.get(field) is None:
                    new_row.append(None)
                else:
                    new_row.append(formatter(row.get(field)))
            ot_log_data["rows"].append(new_row)

        # Make labels
        ot_log_data["labels"] = [
            display_name for field, display_name, formatter in fields
        ]

    return ot_log_data


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    template_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "results.html"
    )
    results_path = os.path.join(output_path, "results.html")

    # Find the csv path
    ot_log_csv_path = os.path.join(archive_path, "onetouch.log")

    ot_log_temp_data = get_ot_log_data(ot_log_csv_path, TARGET_TEMP_FIELDS)
    ot_log_fan_data = get_ot_log_data(ot_log_csv_path, TARGET_FAN_FIELDS)

    # Convert the absolute timestamps to relative time stamps
    for data_set in [ot_log_temp_data, ot_log_fan_data]:
        first_time_stamp = data_set["rows"][0][0]
        for row in data_set["rows"]:
            row[0] -= first_time_stamp

    # Write out results html
    with open(template_path, "r") as template_file:
        with open(results_path, "w") as results_file:
            results_file.write(
                template_file.read()
                .replace('"%raw_temp_data%"', json.dumps(ot_log_temp_data))
                .replace('"%raw_fan_data%"', json.dumps(ot_log_fan_data))
            )

    # Write out status
    return print_info("See results for flow, fan, and temperature plots.")


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
