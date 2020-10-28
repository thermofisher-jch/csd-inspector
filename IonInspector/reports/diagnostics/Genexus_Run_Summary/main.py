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
    tempHeader = "Consumable Information"
    for row in rows:
        if 'Consumable Information' in row:
            other_runDetails[tempHeader] = []
            continue
        if 'Analysis' in row:
            break
        if tempHeader in other_runDetails:
            other_runDetails[tempHeader].append(row)
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