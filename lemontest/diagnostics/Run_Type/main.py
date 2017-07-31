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


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        # get the xml data and look up the run type
        root = get_xml_from_run_log(archive_path)
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

if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
