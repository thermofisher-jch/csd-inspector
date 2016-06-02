#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *

try:
    # get the path to the log file
    archive_path, output_path = sys.argv[1:3]
    run_log_root = get_xml_from_run_log(archive_path)

    # find the name tag by selecting the customer facing name by xpath
    name_tag = run_log_root.find("RunInfo/kit_customer_facing_name")
    if name_tag is None:
        print_alert("No customer facing kit name has been recorded.")
    else:
        print_info(name_tag.text.strip())

except Exception as exc:
    print_na(str(exc))


