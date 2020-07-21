#!/usr/bin/env python

import sys

# from IonInspector.reports.diagnostics.common.inspector_utils import *
from reports.diagnostics.common.inspector_utils import get_chip_names_from_element_tree, get_kit_from_element_tree, \
    get_xml_from_run_log, get_lines_from_chef_gui_logs, print_info, handle_exception


def get_parsed_loadcheck_data(lines):
    loadcheck_key = "parseLoadCheckdata"
    data = {}
    for line in lines:
        if loadcheck_key not in line[2]:
            continue

        loadcheck = line[2].split(":").pop().replace("(", "").replace(")", "").replace(" ", "")
        k, v = loadcheck.split("=")
        data[k] = v

    return data


def execute(archive_path, output_path, archive_type):
    try:
        chef_run_log = get_xml_from_run_log(archive_path)
        chef_gui_log = get_lines_from_chef_gui_logs(archive_path)
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

        loadcheck_data = get_parsed_loadcheck_data(chef_gui_log)

        reagents_lot = loadcheck_data.get("chefReagentsLot", None)
        reagent_expiry = loadcheck_data.get("chefReagentsExpiration", "-")
        if reagents_lot:
            message += " | Reagent Lot: %s (Expiration: %s)" % (reagents_lot, reagent_expiry)

        solutions_lot = loadcheck_data.get("chefSolutionsLot", None)
        solutions_expiry = loadcheck_data.get("chefSolutionsExpiration", "-")
        if solutions_lot:
            message += " | Solutions Lot: %s (Expiration: %s)" % (solutions_lot, solutions_expiry)

        return print_info(message)

    except Exception as e:
        return handle_exception(e, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
