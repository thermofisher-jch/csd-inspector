#!/usr/bin/env python
import os
import json
import ast
from IonInspector.reports.diagnostics.common.inspector_utils import (
    print_info,
    write_results_from_template,
)

AMPLIFICATION_IDX = 1
CYCLE_IDX = 2

def execute(archive_path, output_path, archive_type):
    with open(os.path.join(archive_path, "CSA/planned_run.json")) as fp:
        deck_configs = json.load(fp)["object"]["deckConfig"]

    sample_maps = []
    for config in deck_configs:
        if "sampleBarcodeMapping" in config:
            sample_maps.extend(config["sampleBarcodeMapping"])

        if "pcrProfile" not in config:
            continue

        pcrProfile = config["pcrProfile"]
        if "numTargetAmpCycles" not in pcrProfile:
            pcrProfile["numTargetAmpCycles"] = "-"

        str_literal = pcrProfile.get("amplifyTargetPCRProfile", None)
        if str_literal:
            amplifyTargetPRCProfile = ast.literal_eval(str_literal)
            pcrProfile["numTargetAmpCycles"] = str(amplifyTargetPRCProfile[AMPLIFICATION_IDX][CYCLE_IDX])

    write_results_from_template(
        {"deck_configs": deck_configs, "sample_maps": sample_maps},
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )

    return print_info("See results for details.")
    # return print_info(str(deck_configs[-1]["pcrProfile"]))
