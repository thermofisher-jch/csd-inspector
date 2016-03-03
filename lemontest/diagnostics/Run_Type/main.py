#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *

run_types = {
    "rc": "Chef Templating Run",
    "rl": "Chef Library Prep Run",
    "rd": "Chef gDNA to Chip Run",
    "cleaning": "Chef UV Clean",
    "factorytest": "Factory Test",
    "installtest": "Install Test",
}

try:
    archive, output = sys.argv[1:3]
    file_count = 0
    output_name = ''

    # get the xml data and look up the run type
    root = get_xml_from_run_log(archive)
    run_type_node = root.find("RunInfo/RunType")
    if run_type_node is None:
        raise Exception("No run type")

    # get a groomed version of the output name and find it in the run type map
    output_name = run_type_node.text.strip().lower()
    summary = run_types.get(output_name) if output_name in run_types else 'Other'

    # print the results
    print_info(summary)

except Exception as exc:
    print_na(str(exc))
