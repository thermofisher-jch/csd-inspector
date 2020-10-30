#!/usr/bin/env python

import sys
import glob
import csv


from IonInspector.reports.diagnostics.common.inspector_utils import *
from reports.diagnostics.common.inspector_utils import parse_run_date_from_xml_path

RUN_TYPES = {
    "rc": "Chef Templating Run",
    "rl": "Chef Library Prep Run",
    "rd": "Chef gDNA to Chip Run",
    "cleaning": "Chef UV Clean",
    "factorytest": "Factory Test",
    "installtest": "Install Test",
    "fullloadcheck": "Full Load Check",
}

# See https://stash.amer.thermo.com/projects/CHEF/repos/chef/browse/GUI/gui/OverrideWorkflowWindow.cpp
# for a list of possible RUN_DEVIATIONS

RUN_DEVIATIONS = {
    "default": None,
    "denature30_cycles45_20": "Myeloid",
    "denature30_45_20": "Myeloid",
    "no10xab": "Whole Transcriptome",
    "hid_snp_510_200bp": "HID",
    "pcr400bp": "400bp",
    "pcr200bp": "200bp",
    "anneal62no10xab": "HID",
    "myeloid_protocol": "Myeloid",
    "550_ocav4_short_protocol": "2 Library Pools - OCA Plus",
}


def get_deviation_from_element_tree(element_tree):
    deviation = None
    deviation_node = element_tree.find("RunInfo/deviation")
    if deviation_node is not None:
        key = deviation_node.text.strip().lower()
        if key in RUN_DEVIATIONS:
            deviation = RUN_DEVIATIONS[key]
        else:
            deviation = "Unknown({})".format(key)

    lib = None
    lib_node = element_tree.find("RunInfo/lib")
    if lib_node is not None:
        lib = lib_node.text.strip()
        if lib.isdigit():
            lib += "bp"

    if deviation and lib:
        return "{} ({})".format(deviation, lib)
    elif deviation:
        return deviation
    elif lib:
        return lib
    else:
        return None


def get_cycles_and_extend(element_tree):
    type_node = element_tree.find("RunInfo/RunType")
    if type_node.text.strip() != "rl":
        return None, None

    cycles = None
    cycles_node = element_tree.find("RunInfo/cycles")
    if cycles_node is not None:
        cycles = cycles_node.text.strip()

    extend = None
    extend_node = element_tree.find("RunInfo/extend")
    if extend_node is not None:
        extend = extend_node.text.strip()

    return cycles, extend


def get_libPrepPoolInfo(rows):
    pool = {}
    for i, row in enumerate(rows):
        if row:
            if "lc_lib_combined_bc" in row:
                pool2index = row.index("lc_lib_combined_bc")
                pool["libPool2"] = rows[i + 1][pool2index]
            if "lc_empty_insert_c_bc" in row:
                pool1index = row.index("lc_empty_insert_c_bc")
                pool["libPool1"] = rows[i + 1][pool1index]
                break
    return pool


def get_libPrepProtocal(archive_path):
    run_log_csv_filepath = None
    info_rows = []

    # Find the csv path
    for file_name in glob(
            os.path.join(archive_path, "var", "log", "IonChef", "Data", "lc_runlog.csv")
    ):
        run_log_csv_filepath = file_name
        break

    if not run_log_csv_filepath:
        # return empty dict when not found
        return {}

    with open(run_log_csv_filepath, "rb") as fp:
        # check for NULL in line
        info_rows = list(
            csv.reader((line.replace("\0", "") for line in fp), delimiter=",")
        )

    return get_libPrepPoolInfo(info_rows)


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        # get the xml data and look up the run type
        root = get_xml_from_run_log(archive_path)
        run_type_node = root.find("RunInfo/RunType")
        if run_type_node is None:
            raise Exception("No run type")

        # get cycles and extend
        cycles, extend = get_cycles_and_extend(root)

        # see if there was a deviation
        deviation = get_deviation_from_element_tree(root)

        # get a groomed version of the output name and find it in the run type map
        output_name = run_type_node.text.strip().lower()
        summary = RUN_TYPES.get(output_name) if output_name in RUN_TYPES else "Other"

        # add date from xml filename
        run_log_path = get_chef_run_log_xml_path(archive_path)
        run_date = parse_run_date_from_xml_path(run_log_path)

        # print the results
        message = summary + " | " + run_date.strftime("%-d %b %Y %H:%M") or "Unknown"

        if deviation:
            message += " | Protocol: " + deviation

        if cycles:
            message += " | Cycles: " + cycles

        if extend:
            message += " | Anneal/Extend (min): " + extend

        os.path.join(os.path.dirname(os.path.realpath(__file__)), "results.html")
        os.path.join(output_path, "results.html")
        pool = get_libPrepProtocal(archive_path)

        template_context = {
            "runType": summary,
            "run_date": run_date,
            "Cycles": cycles,
            "extend": extend,
            "deviation": deviation,
        }
        if deviation and "OCA Plus" in deviation:
            template_context["libPool1"] = pool.get("libPool1", "N/A")
            template_context["libPool2"] = pool.get("libPool2", "N/A")

        write_results_from_template(
            template_context, output_path, os.path.dirname(os.path.realpath(__file__))
        )

        return print_info(message)

    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
