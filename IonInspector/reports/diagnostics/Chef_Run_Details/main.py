#!/usr/bin/env python

import sys
from datetime import datetime

from IonInspector.reports.diagnostics.common.inspector_utils import *

RUN_TYPES = {
    "rc": "Chef Templating Run",
    "rl": "Chef Library Prep Run",
    "rd": "Chef gDNA to Chip Run",
    "cleaning": "Chef UV Clean",
    "factorytest": "Factory Test",
    "installtest": "Install Test",
    "fullloadcheck": "Full Load Check"
}

RUN_DEVIATIONS = {
    "default": None,
    "denature30_cycles45_20": "Myeloid",
    "denature30_45_20": "Myeloid",
    "no10xab": "Whole Transcriptome",
    "hid_snp_510_200bp": "HID"
}


def get_deviation_from_element_tree(element_tree):
    deviation_node = element_tree.find("RunInfo/deviation")
    if deviation_node is not None:
        key = deviation_node.text.strip().lower()
        if key in RUN_DEVIATIONS:
            return RUN_DEVIATIONS[key]
        else:
            return "Unknown({})".format(key)
    else:
        return None


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

        # see if there was a deviation
        deviation = get_deviation_from_element_tree(root)

        # get a groomed version of the output name and find it in the run type map
        output_name = run_type_node.text.strip().lower()
        summary = RUN_TYPES.get(output_name) if output_name in RUN_TYPES else 'Other'

        # add date from xml filename
        run_log_path = get_chef_run_log_xml_path(archive_path)
        run_date = parse_run_date_from_xml_path(run_log_path)

        # print the results
        message = summary + " | " + run_date.strftime("%-d %b %Y %H:%M") or "Unknown"

        if deviation:
            message += " | Deviation: " + deviation

        return print_info(message)

    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
