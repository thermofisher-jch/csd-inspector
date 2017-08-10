#!/usr/bin/env python

import sys

from lemontest.diagnostics.common.inspector_utils import *


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
    chef_run_log = get_xml_from_run_log(archive_path)
    chip_a, chip_b = get_chip_names_from_element_tree(chef_run_log)

    message = "Chip 1: %s" % chip_a or "Unknown"
    if chip_b:
        message += ", Chip 2: %s" % chip_b

    print_info(message)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
