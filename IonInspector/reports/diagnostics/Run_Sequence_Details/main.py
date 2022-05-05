#!/usr/bin/env python

import sys
import os
import json
import csv

from dateutil.parser import parse
from datetime import datetime
import matplotlib
if os.environ.get('DISPLAY','') == '':
    print('no display found. Using non-interactive Agg backend')
    matplotlib.use('Agg')
import logging
import fnmatch
import matplotlib.pyplot as plt
from reports.diagnostics.common.inspector_utils import (
    read_explog,
    check_supported,
    get_ts_version,
    write_results_from_template,
    handle_exception,
    print_info,
    read_flow_info_from_explog,
)

logger = logging.getLogger(__name__)


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
    if 0 in flow_data:
        """Accumulate each delta between consecutive time points, but
        until IO-445 is resolved, also be careful to work around
        any data points potentially overwritten by ErrorLogOutput
        near end-of-file."""
        row_count = len(flow_data)
        ii = 0
        last_time = None
        while ii < (row_count - 1) and last_time is None:
            last_time = parse_flow_time(flow_data[ii])
            ii = ii + 1
        # The ii counter may have gaps after any overwritten datapoints
        # have been dropped from consideration.  Keep a second counter, jj,
        # that is only incremented when a data point is used so it may
        # be used for a sequence counter with no gaps.
        jj = 1
        for ii in range(ii, row_count):
            next_time = parse_flow_time(flow_data[ii])
            if next_time is None:
                continue
            time_delta = next_time - last_time
            last_time = next_time
            time_stamp.append([jj, time_delta.seconds])
            jj = jj + 1
    return time_stamp


def parse_flow_time(flow_item):
    time_format = "%H:%M:%S"
    raw_value = flow_item.get("time")
    token_count = len(raw_value)
    if token_count == 1:
        return datetime.strptime(raw_value[token_count - 1], time_format)
    if token_count == 2:
        """This indicates the datapoint was overwritten by an error log entry
        and we don't actually know what the correct value was."""
        return None
    raise ValueError("Every flow record must have a timestamp")


def get_disk_perc(flow_data):
    return [
        [ii, int(flow_data[ii].get("diskPerFree")[0])]
        for ii in flow_data
        if "diskPerFree" in flow_data[ii]
    ]

def CreateInitFillGraphs(archive_path,output_path):
    for file in "initFill_R1","initFill_R2","initFill_R3","initFill_R4","initFill_RW1":
        fileName=os.path.join(os.path.join(archive_path, "CSA"),file)+".csv"
        if os.path.exists(fileName):
            x = []
            y1 = []
            y2 = []
        
            with open(fileName,'r') as csvfile:
                lines = csv.reader(csvfile, delimiter=',')
                for row in lines:
                    x.append(float(row[5]))
                    y1.append(float(row[9]))
                    y2.append(float(row[13]))
                slope=y2[-1]/x[-1]
                fig=plt.figure()
                fig1 = fig.add_subplot(111)
                plt.plot(x, y1, color = 'g', linestyle = 'solid',
                   marker = 'o',label = "WD1")
                plt.plot(x, y2, color = 'r', linestyle = 'solid',
                   marker = 'o',label = "WD2")
        
                plt.xticks(rotation = 15)
                plt.xlabel('Time')
                plt.ylabel('FlowRate')
                plt.title(file+" Rate={:.2f}mL/s".format(slope), fontsize = 20)
                plt.grid()
                plt.legend()
                plt.savefig(os.path.join(output_path,file)+".png")


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

        # try:
        CreateInitFillGraphs(archive_path,output_path)
        # except:
        #     logger.warn("failed to create init fill graphs")
        
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
            "disk_free_perc": disk_free_perc,
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
