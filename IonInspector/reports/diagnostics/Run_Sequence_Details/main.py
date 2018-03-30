#!/usr/bin/env python

import sys

from dateutil.parser import parse

from IonInspector.reports.diagnostics.common.inspector_utils import *

OK_STRING = "TS Version is acceptable at <strong>%s</strong>"
ALERT_STRING = "Advise customer to upgrade their Torrent Server.  Their version is out-dated at <strong>%s</strong>"


def parse_run_number_from_run_name(run_name, device_name):
    if run_name.startswith(device_name):
        run_name = run_name[len(device_name):]
    try:
        return run_name.split("-")[1]
    except Exception as e:
        return "Unknown"


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    try:
        # check that this is a valid hardware set for evaluation
        explog = read_explog(archive_path)
        check_supported(explog)

        ion_params_path = os.path.join(archive_path, 'ion_params_00.json')
        if not os.path.exists(ion_params_path):
            return print_info("Missing ion_params_00.json file. Added in TS 5.0.3.")
        else:
            with open(ion_params_path) as ion_params_handle:
                ion_params = json.load(ion_params_handle)

        version = get_ts_version(archive_path)

        # get the reagent and solution lots and experation dates
        run_date = parse(explog.get('Start Time', 'Unknown'))
        flows = explog.get('Flows', '')
        serial_number = explog.get('Serial Number', 'Unknown')
        system_type = 'PGM ' + explog.get('PGM HW', '') if 'PGM_Run' == archive_type else explog.get('SystemType', '')

        device_name = ion_params.get('exp_json', dict()).get('pgmName', "")

        run_number = str(ion_params.get('exp_json', dict()).get('log', dict()).get('run_number', ""))
        if not run_number:
            run_number = parse_run_number_from_run_name(
                run_name=ion_params.get('exp_json', dict()).get('log', dict()).get('runname', ""),
                device_name=device_name
            )

        datetime_output_format = '%Y/%m/%d'
        template_context = {
            'tss_version': version,
            'device_name': device_name,
            'run_number': run_number,
            'run_date': run_date.strftime(datetime_output_format),
            'flows': flows,
            'serial_number': serial_number,
            'system_type': system_type,
        }
        write_results_from_template(template_context, output_path, os.path.dirname(os.path.realpath(__file__)))

        return print_info(" | ".join([
            "TS " + template_context["tss_version"],
            template_context["device_name"] + " - " + template_context["run_number"],
            template_context["run_date"],
            template_context["flows"] + " flows"
        ]))
    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
