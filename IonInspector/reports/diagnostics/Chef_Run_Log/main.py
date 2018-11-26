#!/usr/bin/env python

import sys
import os
import json
import glob

from IonInspector.reports.diagnostics.common.inspector_utils import print_alert, print_info, print_warning

# Plots  csv header , display header, formatter
from reports.diagnostics.common.inspector_utils import get_run_log_data

TARGET_TEMP_FIELDS = [
    # Time
    ["timestamp", "Time (s)", float],
    # Temps
    ["get_zone1_sample", "Sample Temperature (c)", lambda x: float(x) / 10.0],
    ["get_zone1_block", "Block Temperature (c)", lambda x: float(x) / 10.0],
    ["get_zone1_sink", "Sink Temperature (c)", lambda x: float(x) / 10.0],
    ["get_lid_temp", "PCR Lid Temperature (c)", lambda x: float(x) / 10.0],
    # Reagent Temps sense_reagent	sense_chiller	sense_below	sense_above
    ["sense_reagent", "Reagent Bay Temperature (c)", lambda x: float(x) / 10.0],
    ["sense_chiller", "Chiller Bay Temperature (c)", lambda x: float(x) / 10.0],
    ["sense_below", "Ambient Below Deck Temperature (c)", lambda x: float(x) / 10.0],
    ["sense_above", "Ambient Above Deck Temperature (c)", lambda x: float(x) / 10.0],
]

TARGET_FAN_FIELDS = [
    # Time
    ["timestamp", "Time (s)", float],
    # Flow
    ["tach_flow", "Liquid Cooling Flow Rate (hz)", float],
    # Fans
    ["tach_chassis", "Below Deck Chassis Fan (rev/s)", float],
    ["tach_reagent", "Solutions Cartridge (Front Zone) Fan (rev/s)", float],
    ["tach_chiller", "Reagents Cartridge (Back Zone) Fan (rev/s)", float],
    ["tach_zone1", "Above Deck Fan 1 (rev/s)", float],
    ["tach_zone2", "Above Deck Fan 2 (rev/s)", float],
    ["tach_cfg", "Recovery Centrifuge Motor Fan (10x rev/s)", lambda x: float(x) / 10.0],  # Scaled down so it fits
]


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "results.html")
    results_path = os.path.join(output_path, "results.html")
    run_log_csv_path = None

    # Find the csv path
    for file_name in glob.glob(os.path.join(archive_path, 'var', 'log', 'IonChef', 'RunLog', "*.csv")):
        run_log_csv_path = file_name
        break
    if not run_log_csv_path:
        return print_alert("Could not find RunLog csv!")

    with open(run_log_csv_path) as fp:
        run_log_temp_data = get_run_log_data(fp, TARGET_TEMP_FIELDS)

    with open(run_log_csv_path) as fp:
        run_log_fan_data = get_run_log_data(fp, TARGET_FAN_FIELDS)

    if run_log_temp_data["stages"] or run_log_fan_data["stages"]:
        # Write out results html
        with open(template_path, "r") as template_file:
            with open(results_path, "w") as results_file:
                results_file.write(template_file.read()
                                   .replace("\"%raw_temp_data%\"", json.dumps(run_log_temp_data))
                                   .replace("\"%raw_fan_data%\"", json.dumps(run_log_fan_data))
                                   )

        # Write out status
        return print_info("See results for flow, fan, and temperature plots.")

    else:
        return print_warning("Run log has no rows.")


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
