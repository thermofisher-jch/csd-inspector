#!/usr/bin/env python
import os
import json
import ast
from IonInspector.reports.diagnostics.common.inspector_utils import (
    print_info,
    write_results_from_template,
)

# PCR Profile format:   [temperatures in 0.1 C ], [ durations in sec ], number of time repeated ]
AMPLIFICATION_IDX = -2
CYCLE_IDX = 2


def execute(archive_path, output_path, archive_type):
    with open(os.path.join(archive_path, "CSA/planned_run.json")) as fp:
        deck_configs = json.load(fp)["object"]["deckConfig"]

    # default to false
    column_opts = {
        "annealExtendTime": False,
        "numLibraryAmpCycles": False,
    }

    sample_maps = []
    for config in deck_configs:
        if "sampleBarcodeMapping" in config:
            for sample in config["sampleBarcodeMapping"]:
                sample["sampleInput"] = (
                        float(sample["sampleVolume"])
                        * float(sample["sampleConcentration"])
                        / float(sample["sampleDilutionFactor"])
                )
            sample_maps.extend(config["sampleBarcodeMapping"])

        if "pcrProfile" not in config:
            continue

        # once found, enable
        if "annealExtendTime" in config["pcrProfile"]:
            column_opts["annealExtendTime"] = True

        # once found, enable
        if "numLibraryAmpCycles" in config["pcrProfile"]:
            column_opts["numLibraryAmpCycles"] = True

        pcrProfile = config["pcrProfile"]
        if "numTargetAmpCycles" not in pcrProfile:
            pcrProfile["numTargetAmpCycles"] = "-"

        str_literal = pcrProfile.get("amplifyTargetPCRProfile", None)
        if str_literal:
            amplifyTargetPRCProfile = ast.literal_eval(str_literal)
            pcrProfile["numTargetAmpCycles"] = str(
                amplifyTargetPRCProfile[AMPLIFICATION_IDX][CYCLE_IDX]
            )

    write_results_from_template(
        {
            "deck_configs": deck_configs,
            "sample_maps": sample_maps,
            "column_opts": column_opts,
        },
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )

    return print_info("See results for details.")
