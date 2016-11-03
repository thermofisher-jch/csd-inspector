#!/usr/bin/env python

import sys
import os
import json
import glob
import csv

from lemontest.diagnostics.common.inspector_utils import print_alert, print_info, handle_exception

# Plots  csv header , display header, formatter
TARGET_FIELDS = [
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
    # Temps
    ["get_zone1_sample", "Sample Temperature (c)", lambda x: float(x) / 10.0],
    ["get_zone1_block", "Block Temperature (c)", lambda x: float(x) / 10.0],
    ["get_zone1_sink", "Sink Temperature (c)", lambda x: float(x) / 10.0],
    ["get_lid_temp", "PCR Lid Temperature (c)", lambda x: float(x) / 10.0]
]

archive_path, output_path, device_type = sys.argv[1:4]
template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "results.html")
results_path = os.path.join(output_path, "results.html")
run_log_csv_path = None

# Find the csv path
for file_name in glob.glob(os.path.join(archive_path, 'var', 'log', 'IonChef', 'RunLog', "*.csv")):
    run_log_csv_path = file_name
    break
if not run_log_csv_path:
    print_alert("Could not find RunLog csv!")
    exit()

# Read csv
run_log_data = {
    "stages": [],
    "labels": [],
    "rows": []
}

try:
    with open(run_log_csv_path, "rb") as run_log_csv_file:
        csv_file = csv.DictReader(run_log_csv_file, delimiter=',', quotechar='"')
        current_stage = "START"
        current_stage_start_time = 0
        # Get rows
        for row in csv_file:
            # Add data
            new_row = []
            for field, display_name, formatter in TARGET_FIELDS:
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
        run_log_data["labels"] = [display_name for field, display_name, formatter in TARGET_FIELDS]
except Exception as e:
    handle_exception(e, output_path)
    exit()

# Write out results html
with open(template_path, "r") as template_file:
    with open(results_path, "w") as results_file:
        results_file.write(template_file.read().replace("\"%raw_data%\"", json.dumps(run_log_data)))

# Write out status
print_info("See results for flow, fan, and temperature plots.")
