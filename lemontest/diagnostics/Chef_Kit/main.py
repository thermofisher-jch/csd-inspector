#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    # setup a map for all of the kit names to human readable outputs
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

    try:
        root = get_xml_from_run_log(archive_path)
        name_tag = root.find("RunInfo/kit")
        if name_tag is None:
            raise Exception("No kit info")

        kit_name = name_tag.text.strip()
        print_info(kit_names.get(kit_name, kit_name))

    except Exception as exc:
        print_na(str(exc))

if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
