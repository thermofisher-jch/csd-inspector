#!/usr/bin/env python

import sys
import os
import json
import glob
import csv

from IonInspector.reports.diagnostics.common.inspector_utils import print_alert, print_info, handle_exception

# Plots  csv header , display header, formatter
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


def get_run_log_data(path, fields):
    # Read csv
    run_log_data = {
        "stages": [],
        "labels": [],
        "rows": []
    }

    try:
        with open(path, "rb") as run_log_csv_file:
            csv_file = csv.DictReader(run_log_csv_file, delimiter=',', quotechar='"')
            current_stage = "START"
            current_stage_start_time = 0
            # Get rows
            for row in csv_file:
                # Add data
                new_row = []
                for field, display_name, formatter in fields:
                    if row.get(field) is None:
                        new_row.append(None)
                    else:
                        new_row.append(formatter(row.get(field)))
                run_log_data["rows"].append(new_row)
                # Track the stage intervals
                new_time = float(row['timestamp'])
                new_stage = row["stage0"].upper()
                if current_stage != new_stage:
                    run_log_data["stages"].append({
                        "name": current_stage,
                        "start": current_stage_start_time,
                        "end": new_time
                    })
                    current_stage = new_stage
                    current_stage_start_time = new_time
            # Add final stage
            run_log_data["stages"].append({
                "name": current_stage,
                "start": current_stage_start_time,
                "end": new_time
            })

            # Make labels
            run_log_data["labels"] = [display_name for field, display_name, formatter in fields]
    except Exception as e:
        handle_exception(e, output_path)
        return {}

    return run_log_data


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


    run_log_temp_data = get_run_log_data(run_log_csv_path, TARGET_TEMP_FIELDS)
    run_log_fan_data = get_run_log_data(run_log_csv_path, TARGET_FAN_FIELDS)

    # Write out results html
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
