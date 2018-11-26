#!/usr/bin/env python

import sys
import glob
import os
from IonInspector.reports.diagnostics.common.inspector_utils import print_info, get_run_log_data, print_alert


def seconds_to_hours_minutes(total_seconds):
    m, s = divmod(total_seconds, 60)
    h, m = divmod(m, 60)
    return int(h), int(m)


def get_chef_pause_info(log_lines):
    run_log_stages = get_run_log_data(log_lines).get("stages", [])

    total_time_seconds = None
    if run_log_stages:
        total_time_seconds = run_log_stages[-1]["end"]

    mr_coffee_time_seconds = None
    for stage in run_log_stages:
        if stage["name"] == "MRCOFFEE":
            mr_coffee_time_seconds = stage["end"] - stage["start"]
            break

    pause_time_seconds = None
    for stage in run_log_stages:
        if stage["name"] == "PAUSE":
            pause_time_seconds = stage["end"] - stage["start"]
            break

    message = ""
    if total_time_seconds:
        h, m = seconds_to_hours_minutes(total_time_seconds)
        message += "Total Time: {}h {}m".format(h, m)

    if mr_coffee_time_seconds:
        h, m = seconds_to_hours_minutes(mr_coffee_time_seconds)
        message += " | Mr Coffee: {}h {}m".format(h, m)

    if pause_time_seconds:
        h, m = seconds_to_hours_minutes(pause_time_seconds)
        message += " | User Pause: {}h {}m".format(h, m)

    return message


def execute(archive_path, output_path, archive_type):
    run_log_csv_path = None

    # Find the csv path
    for file_name in glob.glob(os.path.join(archive_path, 'var', 'log', 'IonChef', 'RunLog', "*.csv")):
        run_log_csv_path = file_name
        break
    if not run_log_csv_path:
        return print_alert("Could not find RunLog csv!")

    with open(run_log_csv_path) as fp:
        message = get_chef_pause_info(fp.readlines())

    return print_info(message)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
