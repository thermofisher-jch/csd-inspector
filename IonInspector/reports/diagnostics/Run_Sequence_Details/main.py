#!/usr/bin/env python

import sys
import os
import json

from dateutil.parser import parse
from datetime import datetime

from IonInspector.reports.diagnostics.common.inspector_utils import (
    read_explog,
    check_supported,
    get_ts_version,
    write_results_from_template,
    handle_exception,
    print_info,
    read_flow_info_from_explog
)

OK_STRING = "TS Version is acceptable at <strong>%s</strong>"
ALERT_STRING = "Advise customer to upgrade their Torrent Server.  Their version is out-dated at <strong>%s</strong>"


def parse_run_number_from_run_name(run_name, device_name):
    if run_name.startswith(device_name):
        run_name = run_name[len(device_name) :]
    try:
        return run_name.split("-")[1]
    except Exception as e:
        return "Unknown"


def get_device_name(explog, ion_param_exp):
    if "DeviceName" in explog:
        return explog.get("DeviceName", "")

    if "pgmName" in ion_param_exp:
        return ion_param_exp.get("pgmName", "")

    return ""


def get_system_type(explog, archive_type):
    if archive_type == "PGM_RUN":
        return "PGM %s" % explog.get("PGM HW", "")

    if archive_type == "Valkyrie":
        return explog.get("Platform", "Valkyrie")

    return explog.get("SystemType", "")


def get_flow_time(flow_data):
    time_stamp = []
    time_format = "%H:%M:%S"
    for i in range(len(flow_data)-1):
        time_delta = (datetime.strptime(flow_data[i+1].get("time")[0], time_format) -
                      datetime.strptime(flow_data[i].get("time")[0], time_format))
        time_stamp.append([i, time_delta.seconds])
    return time_stamp


def get_disk_perc(flow_data):
    disk_perc = []
    for i in range(len(flow_data)):
        disk_perc.append([i, int(flow_data[i].get("diskPerFree")[0])])
    return disk_perc


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    try:
        # check that this is a valid hardware set for evaluation
        explog = read_explog(archive_path)
        check_supported(explog)

        ion_params_paths = [
            os.path.join(archive_path, "CSA", "ion_params_00.json"),
            os.path.join(archive_path, "ion_params_00.json"),
        ]
        for ion_params_path in ion_params_paths:
            if os.path.exists(ion_params_path):
                break
        else:
            return print_info("Missing ion_params_00.json file. Added in TS 5.0.3.")

        with open(ion_params_path) as ion_params_handle:
            ion_params = json.load(ion_params_handle)

        version = get_ts_version(archive_path)

        # get the reagent and solution lots and experation dates
        run_date = parse(explog.get("Start Time", "Unknown"))
        flows = explog.get("Flows", "")
        serial_number = explog.get("Serial Number", "Unknown")

        system_type = get_system_type(explog, archive_type)

        exp_json = ion_params.get("exp_json", dict())
        # Fix a valk bug where "exp_json" is sometime a json string instead of the object
        if isinstance(exp_json, basestring):
            exp_json = json.loads(exp_json)

        device_name = get_device_name(explog, exp_json)

        run_number = str(exp_json.get("log", dict()).get("run_number", ""))
        if not run_number:
            run_number = parse_run_number_from_run_name(
                run_name=exp_json.get("log", dict()).get("runname", ""),
                device_name=device_name,
            )

        flow_data = read_flow_info_from_explog(explog)
        flow_time_secs = get_flow_time(flow_data)
        disk_free_perc = get_disk_perc(flow_data)

        datetime_output_format = "%Y/%m/%d"
        template_context = {
            "tss_version": version,
            "device_name": device_name,
            "run_number": run_number,
            "run_date": run_date.strftime(datetime_output_format),
            "flows": flows,
            "serial_number": serial_number,
            "system_type": system_type,
            "flow_time_seconds": flow_time_secs,
            "disk_free_perc": disk_free_perc
        }
        write_results_from_template(
            template_context, output_path, os.path.dirname(os.path.realpath(__file__))
        )

        return print_info(
            " | ".join(
                [
                    "TS " + template_context["tss_version"],
                    template_context["device_name"]
                    + " - "
                    + template_context["run_number"],
                    template_context["run_date"],
                    template_context["flows"] + " flows",
                ]
            )
        )
    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
