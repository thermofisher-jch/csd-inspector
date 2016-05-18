#!/usr/bin/env python

import sys
from lemontest.diagnostics.common.inspector_utils import *

# setup a map for all of the kit names to human readable outputs
kit_names = {
    "pgm_ic_v2": "Ion PGM Hi-Q Chef Kit",
    "pgm_ic_v1": "Ion PGM IC 200 Kit",
    "pi_ic_v1": "Ion PI IC 200 Kit",
    "pi_ic_v2": "Ion PI Hi-Q Chef Kit",
    "s530_1": "Ion 520/530 Kit-Chef",
    "s540_1": "Ion 540 Kit-Chef",
    "as_1": "Ion AmpliSeq Kit for Chef DL8"
}

try:
    archive, output = sys.argv[1:3]

    root = get_xml_from_run_log(archive)
    name_tag = root.find("RunInfo/kit")
    if name_tag is None:
        raise Exception("No kit info")

    kit_name = name_tag.text.strip()
    print_info(kit_names.get(kit_name, kit_name))

except Exception as exc:
    print_na(str(exc))
