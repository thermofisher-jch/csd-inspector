#!/usr/bin/env python

import sys
from IonInspector.reports.diagnostics.common.inspector_utils import *


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        # get the path to the log file
        run_log_root = get_xml_from_run_log(archive_path)

        # find the name tag by selecting the customer facing name by xpath
        name_tag = run_log_root.find("RunInfo/kit_customer_facing_name")
        if name_tag is None:
            return print_alert("No customer facing kit name has been recorded.")
        else:
            return print_info(name_tag.text.strip())

    except Exception as exc:
        return print_na(str(exc))


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
