#!/usr/bin/env python

import sys
from datetime import datetime

from lemontest.diagnostics.common.inspector_utils import *

run_types = {
    "rc": "Chef Templating Run",
    "rl": "Chef Library Prep Run",
    "rd": "Chef gDNA to Chip Run",
    "cleaning": "Chef UV Clean",
    "factorytest": "Factory Test",
    "installtest": "Install Test",
}


def parse_run_date_from_xml_path(path):
    """
    Parse run date from file paths like: "/opt/example/242470284-000327_rl_2017-4-18_1759.xml"
    """
    _, date_str, time_str = path.rsplit("_", 2)
    return datetime.strptime(date_str + "_" + time_str, "%Y-%m-%d_%H%M.xml")


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

        # add date from xml filename
        run_log_path = get_chef_run_log_xml_path(archive_path)
        run_date = parse_run_date_from_xml_path(run_log_path)

        # print the results
        print_info(summary + " | " + run_date.strftime("%-d %b %Y %H:%M") or "Unknown")

    except Exception as exc:
        print_na(str(exc))

if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
