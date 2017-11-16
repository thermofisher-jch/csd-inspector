#!/usr/bin/env python

import sys

from IonInspector.reports.diagnostics.common.inspector_utils import *


def get_kit_from_element_tree(element_tree):
    kit_names = {
        "pgm_ic_v2": "Ion PGM Hi-Q Chef Kit",
        "pgm_ic_v1": "Ion PGM IC 200 Kit",
        "pi_ic_v1": "Ion PI IC 200 Kit",
        "pi_ic_v2": "Ion PI Hi-Q Chef Kit",
        "s530_1": "Ion 520/530 Kit-Chef",
        "s540_1": "Ion 540 Kit-Chef",
        "as_1": "Ion AmpliSeq Kit for Chef DL8",
        "pgm_ionchef_200_kit": "Ion PGM IC 200 Kit",
        "pi_ic200": "Ion PI IC 200 Kit",
        "pgm_3": "Ion PGM Hi-Q View Chef Kit",
        "hid_s530_1": "Ion Chef HID S530 V1",
        "hid_s530_2": "Ion Chef HID S530 V2",
        "hid_as_1": "Ion Chef HID Library V1",
        "hid_as_2": "Ion Chef HID Library V2",
        "s521_1": "Ion 520/530 ExT Kit-Chef V1",
    }

    name_tag = element_tree.find("RunInfo/kit")
    if name_tag is None:
        return None
    kit_name = name_tag.text.strip()
    return kit_names.get(kit_name, kit_name)


def get_chip_names_from_element_tree(element_tree):
    """
    Extract chip name from a chef run log element tree. Two items of note:
    * There may be two chips <chip> and <chip2>
    * For proton chips, the <chip> element only contains the major version number. <chipVersion>
      contains the minor version. So P1v3 would be <chip>1</chip> <chipVersion>3</chipVersion>
    """
    names = [None, None]
    for i, suffix in enumerate(["", "2"]):
        chip_element = element_tree.find("./RunInfo/chip" + suffix)
        chip_version_element = element_tree.find("./RunInfo/chipVersion" + suffix)
        if chip_element is not None:
            if chip_element.text.isdigit() and int(chip_element.text) < 10:
                if chip_version_element is not None:
                    names[i] = "P" + chip_element.text + "v" + chip_version_element.text
            else:
                names[i] = chip_element.text
    return names


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
