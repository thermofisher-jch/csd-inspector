#!/usr/bin/env python

import sys
import os
import json
import datetime

from IonInspector.reports.diagnostics.common.inspector_utils import print_alert, print_info, print_warning

# Plots  csv header , display header, formatter
from reports.diagnostics.common.inspector_utils import get_valk_lib_prep_data


def convert_time(value):
    return float(datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S').strftime('%s'))


TARGET_TEMP_FIELDS = [
    # Time
    ["time", "Time (s)", convert_time],
    # Temps
    ["PCRTemp1", "PCRTemp1", lambda x: float(x)],
    ["PCRTemp2", "PCRTemp2", lambda x: float(x)],
    ["PCRTemp3", "PCRTemp3", lambda x: float(x)],
    ["ChipHeatTemp", "ChipHeatTemp", lambda x: float(x)],
    ["MagSepTemp", "MagSepTemp", lambda x: float(x)],
    ["ReagentBayTemp1", "Zone 1+3 Temp", lambda x: float(x)],
    ["ReagentBayTemp2", "Zone 2+4 Temp", lambda x: float(x)],
]

TARGET_FAN_FIELDS = [
    # Time
    ["time", "Time (s)", convert_time],
    # Fans
    ["ChipFanSpeed", "ChipFanSpeed", float],
]


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "results.html")
    results_path = os.path.join(output_path, "results.html")
    run_log_csv_path = os.path.join(archive_path, "CSA", "libPrep_log.csv")

    if not os.path.exists(run_log_csv_path):
        return print_alert("Could not find libPrep_log.csv!")

    with open(run_log_csv_path) as fp:
        run_log_temp_data = get_valk_lib_prep_data(fp, TARGET_TEMP_FIELDS)

    with open(run_log_csv_path) as fp:
        run_log_fan_data = get_valk_lib_prep_data(fp, TARGET_FAN_FIELDS)

    with open(template_path, "r") as template_file:
        with open(results_path, "w") as results_file:
            results_file.write(template_file.read()
                               .replace("\"%raw_temp_data%\"", json.dumps(run_log_temp_data))
                               .replace("\"%raw_fan_data%\"", json.dumps(run_log_fan_data))
                               )

    # Write out status
    return print_info("See results for flow, fan, and temperature plots.")


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
