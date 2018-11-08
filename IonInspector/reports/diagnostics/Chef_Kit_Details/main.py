#!/usr/bin/env python

import sys

from IonInspector.reports.diagnostics.common.inspector_utils import *
from reports.diagnostics.common.inspector_utils import get_chip_names_from_element_tree, get_kit_from_element_tree


def execute(archive_path, output_path, archive_type):
    try:
        chef_run_log = get_xml_from_run_log(archive_path)
        chip_a, chip_b = get_chip_names_from_element_tree(chef_run_log)

        kit = get_kit_from_element_tree(chef_run_log)
        message = (kit or "Unknown Kit") + " | "

        if chip_a and chip_b:
            message += "Chip 1: %s" % chip_a
            message += ", Chip 2: %s" % chip_b
        elif chip_a:
            message += "Chip: %s" % chip_a
        elif chip_b:
            message += "Chip: %s" % chip_a
        else:
            message += "Unknown Chip"

        return print_info(message)

    except Exception as e:
        return handle_exception(e, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
