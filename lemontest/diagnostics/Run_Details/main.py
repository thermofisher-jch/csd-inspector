#!/usr/bin/env python

import json
import sys
import os
from dateutil.parser import parse
from lemontest.diagnostics.common.inspector_utils import *

OK_STRING = "TS Version is acceptable at <strong>%s</strong>"
ALERT_STRING = "Advise customer to upgrade their Torrent Server.  Their version is out-dated at <strong>%s</strong>"


def format_run_date(raw_string):
    try:
        run_date = parse(raw_string)
    except Exception as e:
        return "Unknown"
    return run_date.strftime("%d %b %Y")


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    try:
        # check that this is a valid hardware set for evaluation
        explog = read_explog(archive_path)
        check_supported(explog)

        with open(os.path.join(archive_path, 'ion_params_00.json')) as ion_params_handle:
            ion_params = json.load(ion_params_handle)

        version_path = os.path.join(archive_path, "version.txt")
        if not os.path.exists(version_path):
            raise Exception("Missing file: " + version_path)

        # get the version number
        line = open(version_path).readline()
        version = line.split('=')[-1].strip()
        version = version.split()[0]

        write_results_from_template({
            'tss_version': version,
            'device_name': ion_params.get('exp_json', dict()).get('pgmName', dict()),
            'run_number': ion_params.get('exp_json', dict()).get('log', dict()).get('run_number', 'Unknown'),
            'run_date': format_run_date(explog.get('Start Time', 'Unknown')),
            'chef_name': ion_params.get('exp_json', dict()).get('chefInstrumentName', ''),
            'sample_pos': ion_params.get('exp_json', dict()).get('chefSamplePos', ''),
        }, output_path)

        details = "See results"
        print_info(details)
    except Exception as exc:
        handle_exception(exc, output_path)

if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
