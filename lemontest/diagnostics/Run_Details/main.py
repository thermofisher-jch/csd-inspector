#!/usr/bin/env python

import sys
from datetime import datetime

from dateutil.parser import parse

from lemontest.diagnostics.common.inspector_utils import *

OK_STRING = "TS Version is acceptable at <strong>%s</strong>"
ALERT_STRING = "Advise customer to upgrade their Torrent Server.  Their version is out-dated at <strong>%s</strong>"


def execute(archive_path, output_path, archive_type):
    """Executes the test"""

    try:
        # check that this is a valid hardware set for evaluation
        explog = read_explog(archive_path)
        check_supported(explog)

        with open(os.path.join(archive_path, 'ion_params_00.json')) as ion_params_handle:
            ion_params = json.load(ion_params_handle)

        version = get_ts_version(archive_path)

        # get the reagent and solution lots and experation dates
        run_date = parse(explog.get('Start Time', 'Unknown'))
        flows = explog.get('Flows', '')
        chef_reagents_lot = ion_params.get('exp_json', dict()).get('chefReagentsLot', '')
        chef_reagents_expiration = ion_params.get('exp_json', dict()).get('chefReagentsExpiration', '')
        chef_reagents_expiration = datetime.strptime(chef_reagents_expiration, '%y%m%d') if chef_reagents_expiration else None
        chef_solutions_lot = ion_params.get('exp_json', dict()).get('chefSolutionsLot', '')
        chef_solutions_expiration = ion_params.get('exp_json', dict()).get('chefSolutionsExpiration', '')
        chef_solutions_expiration = datetime.strptime(chef_solutions_expiration, '%y%m%d') if chef_solutions_expiration else None

        datetime_output_format = '%Y/%m/%d'
        write_results_from_template({
            'tss_version': version,
            'device_name': ion_params.get('exp_json', dict()).get('pgmName', dict()),
            'run_number': ion_params.get('exp_json', dict()).get('log', dict()).get('run_number', 'Unknown'),
            'run_date': run_date.strftime(datetime_output_format),
            'flows': flows,
            'chef_name': ion_params.get('exp_json', dict()).get('chefInstrumentName', ''),
            'sample_pos': ion_params.get('exp_json', dict()).get('chefSamplePos', ''),
            'chef_reagents_lot': chef_reagents_lot,
            'chef_reagents_expiration': chef_reagents_expiration.strftime(datetime_output_format) if chef_reagents_expiration else '',
            'chef_solutions_lot': chef_solutions_lot,
            'chef_solutions_expiration': chef_solutions_expiration.strftime(datetime_output_format) if chef_solutions_expiration else ''
        }, output_path)

        if chef_reagents_expiration and chef_reagents_expiration < run_date:
            print_alert("Chef reagents and/or solutions used were expired.  See results for details.")
        elif chef_solutions_expiration and chef_solutions_expiration < run_date:
            print_alert("Chef reagents and/or solutions used were expired.  See results for details.")
        else:
            print_info("See results for details.")
    except Exception as exc:
        handle_exception(exc, output_path)

if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
