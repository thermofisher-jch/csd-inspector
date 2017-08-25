#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import sys
from lemontest.diagnostics.common.inspector_utils import *


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        params_path = os.path.join(archive_path, 'ion_params_00.json')
        # read the ion params file
        params = dict()
        if os.path.exists(params_path):
            with open(params_path) as params_file:
                params = json.load(params_file)

        if params.get("exp_json", {}).get("chefKitType"):
            template_kit_name = params.get("exp_json", {}).get("chefKitType")
        elif 'plan' in params and 'templatingKitName' in params['plan']:
            template_kit_name = params['plan']['templatingKitName']
        else:
            template_kit_name = "Unknown Templating Kit"

        # get the sequencing kit description from the exp log
        exp_log = read_explog(archive_path)
        inspector_seq_kit = exp_log.get("SeqKitDesc", None) or exp_log.get("SeqKitPlanDesc", None) or "Unknown Sequencing Kit"

        # get the system type
        system_type = "Unknown System Type"
        if "SystemType" in exp_log:
            system_type = exp_log.get("SystemType")
        elif "PGM HW" in exp_log:
            system_type = "PGM" + exp_log.get("PGM HW")

        # print the details
        print_info(" | ".join([system_type, inspector_seq_kit, template_kit_name]))

    except Exception as exc:
        print_failed(str(exc))

if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
