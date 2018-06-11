#!/usr/bin/env python

import sys
from datetime import datetime

from dateutil.parser import parse

from IonInspector.reports.diagnostics.common.inspector_utils import *

OK_STRING = "TS Version is acceptable at <strong>%s</strong>"
ALERT_STRING = "Advise customer to upgrade their Torrent Server.  Their version is out-dated at <strong>%s</strong>"


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    try:
        try:
            if not run_used_chef(archive_path):
                return print_na("Ion Chef was not used for this run.")
        except ValueError:
            return print_na("Could not find ion_params_00.json.")

        # check that this is a valid hardware set for evaluation
        explog = read_explog(archive_path)
        check_supported(explog)

        ion_params_path = os.path.join(archive_path, 'ion_params_00.json')
        if not os.path.exists(ion_params_path):
            return print_na("Could not find ion_params_00.json.")

        with open(ion_params_path) as ion_params_handle:
            ion_params = json.load(ion_params_handle)

        # get the reagent and solution lots and experation dates
        run_date = parse(explog.get('Start Time', 'Unknown'))
        chef_reagents_lot = ion_params.get('exp_json', dict()).get('chefReagentsLot', '')
        chef_reagents_expiration = ion_params.get('exp_json', dict()).get('chefReagentsExpiration', '')
        try:
            chef_reagents_expiration = datetime.strptime(chef_reagents_expiration,
                                                     '%y%m%d') if chef_reagents_expiration else None
        except:
            chef_reagents_expiration = None
        chef_solutions_lot = ion_params.get('exp_json', dict()).get('chefSolutionsLot', '')
        chef_solutions_expiration = ion_params.get('exp_json', dict()).get('chefSolutionsExpiration', '')
        try:
            chef_solutions_expiration = datetime.strptime(chef_solutions_expiration,
                                                      '%y%m%d') if chef_solutions_expiration else None
        except:
            chef_solutions_expiration = None

        datetime_output_format = '%Y/%m/%d'
        template_context = {
            'run_date': run_date.strftime(datetime_output_format),
            'chef_name': ion_params.get('exp_json', dict()).get('chefInstrumentName', ''),
            'sample_pos': ion_params.get('exp_json', dict()).get('chefSamplePos', ''),
            'chef_reagents_lot': chef_reagents_lot,
            'chef_reagents_expiration': chef_reagents_expiration.strftime(
                datetime_output_format) if chef_reagents_expiration else '',
            'chef_solutions_lot': chef_solutions_lot,
            'chef_solutions_expiration': chef_solutions_expiration.strftime(
                datetime_output_format) if chef_solutions_expiration else ''
        }
        write_results_from_template(template_context, output_path, os.path.dirname(os.path.realpath(__file__)))

        message = template_context["chef_name"] + " Sample " + \
                  template_context["sample_pos"] + " | " + \
                  "Reagents Lot " + template_context["chef_reagents_lot"] + " | " + \
                  "Solutions Lot " + template_context["chef_solutions_lot"]

        if not chef_reagents_expiration or not chef_solutions_expiration:
            return print_alert(message + " | Could not parse expiration dates.")
        elif chef_reagents_expiration and chef_reagents_expiration < run_date:
            return print_alert(message + " | Expired Reagents")
        elif chef_solutions_expiration and chef_solutions_expiration < run_date:
            return print_alert(message + " | Expired Reagents")
        else:
            return print_ok(message)
    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
