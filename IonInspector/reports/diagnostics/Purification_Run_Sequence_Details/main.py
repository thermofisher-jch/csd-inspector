#!/usr/bin/env python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import sys
import os
import json
import csv
import subprocess
from dateutil.parser import parse
from datetime import datetime
import logging
import fnmatch
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




def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    try:
        cmd="find " + archive_path + " -name Quant_summary.csv | head -n 1"
        try:
            filename=subprocess.check_output(cmd,shell=True).decode()
        except:
            filename=""
        logger.warn("got back : "+filename)
    
        if filename == "":
            return print_info("NA")
        explog = read_explog(os.path.dirname(filename.strip()))
        version = explog.get("Extraction instrument Release_version","Unknown")
        run_date = parse(explog.get("Start Time", "Unknown"))
        flows = explog.get("Flows", "")
        serial_number = explog.get("Serial Number", "Unknown")
        system_type = "Genexus Purification"
        device_name = explog.get("DeviceName","Unknown")
        run_number = str(explog.get("uid","0"))
        datetime_output_format = "%Y/%m/%d"
        template_context = {
            "tss_version": version,
            "device_name": device_name,
            "run_number": run_number,
            "run_date": run_date.strftime(datetime_output_format),
            "serial_number": serial_number,
            "system_type": system_type,
        }
        rsltName="results.html"
        write_results_from_template(
            template_context, output_path, os.path.dirname(os.path.realpath(__file__)), templateName=rsltName
        )

        return print_info(
            " | ".join(
                [
                    "TS " + template_context["tss_version"],
                    template_context["device_name"]
                    + " - "
                    + template_context["run_number"],
                    template_context["run_date"],
                ]
            )
        )
    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
