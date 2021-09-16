# -*- coding: utf-8 -*-
#!/usr/bin/env python
import os
import csv
import fnmatch
import copy
from IonInspector.reports.diagnostics.common.inspector_utils import (
    print_info,
    print_alert,
    print_ok,
    write_results_from_template,
)


def get_other_details(rows):
    other_runDetails = {}
    consumable = "Consumable Information"
    reagent = "Reagent Information"
    for row in rows:
        if reagent in row:
            other_runDetails[reagent] = []
            continue
        if (
            reagent in other_runDetails
            and consumable not in row
            and consumable not in other_runDetails
        ):
            other_runDetails[reagent].append(row)
        if consumable in row:
            other_runDetails[consumable] = []
            continue
        if consumable in other_runDetails and "Analysis" not in row:
            other_runDetails[consumable].append(row)
        if "Analysis" in row:
            break
    return other_runDetails


def execute(archive_path, output_path, archive_type):
    infoRowsForOtherDetails = None
    for root, dirnames, filenames in os.walk(os.path.join(archive_path, "CSA")):
        for filename in fnmatch.filter(filenames, "Info.csv"):
            with open(os.path.join(root, filename), "rb") as fp:
                info_rows = list(csv.reader(fp, delimiter=","))
                infoRowsForOtherDetails = copy.deepcopy(info_rows)

    write_results_from_template(
        {"other_runDetails": get_other_details(infoRowsForOtherDetails)},
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )

    return print_info("See results for details.")
